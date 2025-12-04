import re
import string
import struct


TIME_RE = re.compile(rb"^[0-2][0-9]:[0-5][0-9]$")


class ProtobufParser:
    """
    Recursive protobuf-like tokenizer producing a nested tree (self.tree)
    plus a compact nested list (self.compact) with simplified values.

    Compact representation rules:
      - Submessage -> list([...])
      - Primitive varint / 32-bit / 64-bit -> int
      - Length-delimited printable UTF-8 -> str
      - Time (HH:MM) -> str
      - Otherwise -> {'field': int, 'wire_type': int, 'hex': str, 'len': int}
    """

    def __init__(self, blob: bytes):
        self.original = blob
        self.tree = self._parse_message(blob)
        self.id = None
        self.date = None
        if self.tree:
            if self.tree[0]['wire_type'] == 0:
                self.id = self.tree[0].get('decoded')
            if len(self.tree) > 1 and self.tree[1]['wire_type'] == 2:
                if isinstance(self.tree[1].get('decoded'), str):
                    self.date = self.tree[1]['decoded']
        # Build compact representation
        self.compact = self._compact_list(self.tree)

    def __str__(self):
        return f"HoymilesParser(id={self.id}, date={self.date}, root_fields={len(self.tree)})"

    # -------- Public API --------

    def recursive_fields(self):
        return self.tree

    def get_compact(self):
        return self.compact

    def collect_times(self):
        return [
            f['value_bytes'].decode('ascii')
            for f in self._walk(self.tree)
            if f.get('is_time')
        ]

    def debug_print_tree(self, max_depth=5):
        lines = []
        for f in self._walk(self.tree):
            depth = f['_depth']
            if depth > max_depth:
                continue
            indent = '  ' * depth
            extras = []
            if f.get('is_time'):
                extras.append("TIME")
            if 'subfields' in f:
                extras.append(f"sub=%d" % len(f['subfields']))
            if 'decoded' in f and f.get('decoded') is not None and not f.get('is_time'):
                dv = f['decoded']
                if isinstance(dv, (bytes, bytearray)):
                    dv_show = dv[:16]
                    if len(dv) > 16:
                        dv_show = dv_show + b"..."
                    extras.append(f"dec={dv_show!r}")
                else:
                    extras.append(f"dec={dv!r}")
            vb = f['value_bytes']
            show = vb[:24]
            if len(vb) > 24:
                show = show + b'...'
            lines.append(f"{indent}F{f['field']} wt={f['wire_type']} len={len(vb)} {' '.join(extras)} val={show}")
        return "\n".join(lines)

    # -------- Recursive parsing --------

    def _parse_message(self, data: bytes, depth: int = 0, max_fields: int = 100000):
        offset = 0
        fields = []
        for _ in range(max_fields):
            if offset >= len(data):
                break
            start = offset
            try:
                key, offset = self._read_varint(data, offset)
            except Exception:
                break
            field_number = key >> 3
            wire_type = key & 0x07
            try:
                if wire_type == 0:  # varint
                    _, off2 = self._read_varint(data, offset)
                    value_bytes = data[offset:off2]
                    offset = off2
                elif wire_type == 1:  # 64-bit
                    value_bytes = data[offset:offset+8]
                    if len(value_bytes) < 8:
                        break
                    offset += 8
                elif wire_type == 2:  # length-delimited
                    length, off2 = self._read_varint(data, offset)
                    vs = off2
                    ve = vs + length
                    if ve > len(data):
                        break
                    value_bytes = data[vs:ve]
                    offset = ve
                elif wire_type == 5:  # 32-bit
                    value_bytes = data[offset:offset+4]
                    if len(value_bytes) < 4:
                        break
                    offset += 4
                else:
                    break
            except Exception:
                break

            end = offset
            node = {
                'field': field_number,
                'wire_type': wire_type,
                'value_bytes': value_bytes,
                'raw': data[start:end],
                'start': start,
                'end': end,
                '_depth': depth,
            }

            # Primitive decode
            node['decoded'] = self._decode_primitive(node)

            # Mark time strings
            if wire_type == 2 and len(value_bytes) == 5 and TIME_RE.match(value_bytes):
                try:
                    value_bytes.decode('ascii')
                    node['is_time'] = True
                except Exception:
                    pass

            # Attempt recursive parse for length-delimited (if not time and not a simple decoded string)
            if wire_type == 2 and not node.get('is_time') and not (
                isinstance(node.get('decoded'), str) and len(value_bytes) == len(node['decoded'])
            ):
                sub = self._attempt_subparse(value_bytes, depth + 1)
                if sub is not None:
                    node['subfields'] = sub

            fields.append(node)
        return fields

    def _attempt_subparse(self, value: bytes, depth: int):
        subfields = self._parse_message(value, depth=depth)
        if not subfields:
            return None
        if subfields[-1]['end'] != len(value):
            return None
        return subfields

    # -------- Compact conversion --------

    def _compact_list(self, nodes):
        compact = []
        for n in nodes:
            # If submessage
            if 'subfields' in n:
                compact.append(self._compact_list(n['subfields']))
                continue

            # Primitive (int) or decoded string/time
            decoded = n.get('decoded')

            # If we have a decoded primitive (int) from wire types 0/1/5
            if decoded is not None and n['wire_type'] in (0, 1, 5) and not isinstance(decoded, (bytes, bytearray)):
                compact.append(decoded)
                continue

            # Time always as string
            if n.get('is_time'):
                try:
                    compact.append(n['value_bytes'].decode('ascii'))
                    continue
                except Exception:
                    pass  # fallback to dict

            # Decoded printable string
            if isinstance(decoded, str):
                compact.append(decoded)
                continue

            # Fallback: minimal dict
            vb = n['value_bytes']
            compact.append({
                'field': n['field'],
                'wire_type': n['wire_type'],
                'hex': vb.hex(),
                'len': len(vb),
            })
        return compact

    # -------- Decoding helpers --------

    def _decode_primitive(self, node):
        wt = node['wire_type']
        vb = node['value_bytes']
        try:
            if wt == 0:  # varint
                return self._decode_varint_bytes(vb)
            if wt == 1 and len(vb) == 8:  # 64-bit little endian
                return int.from_bytes(vb, 'little', signed=False)
            if wt == 5 and len(vb) == 4:  # 32-bit little endian
                return int.from_bytes(vb, 'little', signed=False)
            if wt == 2:  # length-delimited; attempt UTF-8 text
                return self._maybe_decode_length_delimited(vb)
        except Exception:
            return None
        return None

    def _maybe_decode_length_delimited(self, b: bytes):
        if not b:
            return ""
        try:
            txt = b.decode('utf-8')
        except UnicodeDecodeError:
            return None
        printable_ratio = sum(ch in string.printable for ch in txt) / max(1, len(txt))
        if printable_ratio < 0.6:
            return None
        return txt

    # -------- Traversal --------

    def _walk(self, nodes):
        for n in nodes:
            yield n
            if 'subfields' in n:
                yield from self._walk(n['subfields'])

    # -------- Low-level varint helpers --------

    def _read_varint(self, data: bytes, offset: int):
        shift = 0
        result = 0
        while True:
            if offset >= len(data):
                raise ValueError("Truncated varint")
            b = data[offset]
            result |= (b & 0x7F) << shift
            offset += 1
            if not (b & 0x80):
                break
            shift += 7
            if shift > 63:
                raise ValueError("Varint too long")
        return result, offset

    def _decode_varint_bytes(self, b: bytes):
        shift = 0
        result = 0
        for by in b:
            result |= (by & 0x7F) << shift
            if not (by & 0x80):
                return result
            shift += 7
        return result
    
    @staticmethod
    def decode_data_point(data_point: list):
        decoded = []
        for i, val in enumerate(data_point):
            if isinstance(val, (int, float)) and val < 10:
                decoded.append(val)
            elif isinstance(val, (int, float)):
                decoded.append(struct.unpack('<f', struct.pack('<I', val))[0])
            else:
                # Skip non-numeric values
                continue
        return decoded
