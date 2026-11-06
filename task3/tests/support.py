import json

from task3_streaming.redaction import Processor


def wire(name, payload, newline=b"\n", *, ascii_json=True):
    return (
        b"event: "
        + name.encode()
        + newline
        + b"data: "
        + json.dumps(payload, ensure_ascii=ascii_json, separators=(",", ":")).encode()
        + newline
        + newline
    )


def stream(text, channel=0, *, ascii_json=True):
    return (
        wire("delta", {"channel": channel, "text": text}, ascii_json=ascii_json)
        + wire("done", {"channel": channel})
        + wire("end", {})
    )


def output(frames):
    events = []
    for frame in frames:
        assert frame.endswith(b"\n\n")
        lines = frame[:-2].decode("utf-8").split("\n")
        assert len(lines) == 2 and lines[0].startswith("event: ")
        assert lines[1].startswith("data: ")
        events.append((lines[0][7:], json.loads(lines[1][6:])))
    return events


def text_output(frames, channel=0):
    return "".join(v["text"] for k, v in output(frames) if k == "delta" and v["channel"] == channel)


def run(raw, sizes=None, processor=None):
    processor = processor or Processor()
    frames = []
    if sizes is None:
        sizes = [4096] * (len(raw) // 4096 + 1)
    offset = 0
    for size in sizes:
        frames.extend(processor.feed(raw[offset : offset + size]))
        offset += size
    assert offset >= len(raw)
    frames.extend(processor.finish())
    return frames


def reference(text):
    """Independent whole-input oracle: manual interval checks, no production regex."""
    alphabet = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+@-")

    def digits(value):
        return bool(value) and all("0" <= c <= "9" for c in value)

    def numeric(value):
        return (
            bool(value)
            and digits(value[0])
            and digits(value[-1])
            and all(
                digits(c) or (c in " -" and digits(value[i - 1]) and digits(value[i + 1]))
                for i, c in enumerate(value)
            )
        )

    def sensitive(token):
        if "@" in token:
            return True
        cursor = 0
        while cursor < len(token):
            if not digits(token[cursor]):
                cursor += 1
                continue
            end, count = cursor + 1, 1
            while end < len(token):
                if digits(token[end]):
                    count += 1
                    end += 1
                elif token[end] in " -" and end + 1 < len(token) and digits(token[end + 1]):
                    end += 1
                else:
                    break
            if 13 <= count <= 19:
                return True
            cursor = end
        for start in range(len(token)):
            for size in [11, 12, *range(9, 17)]:
                end = start + size
                if end > len(token):
                    continue
                item = token[start:end]
                if (start and digits(token[start - 1])) or (
                    end < len(token) and digits(token[end])
                ):
                    continue
                ssn = (
                    size == 11
                    and item[3] == item[6] == "-"
                    and digits(item[:3] + item[4:6] + item[7:])
                )
                us = (
                    size == 12
                    and item[3] == item[7] == "-"
                    and digits(item[:3] + item[4:7] + item[8:])
                )
                international = (
                    item.startswith("+")
                    and "1" <= item[1] <= "9"
                    and 8 <= len(item[1:]) <= 15
                    and digits(item[1:])
                )
                if ssn or us or international:
                    return True
        return False

    result = []
    start = 0
    while start < len(text):
        end = start
        if text[start] not in alphabet:
            result.append(text[start])
            start += 1
            continue
        while end < len(text):
            if text[end] in alphabet:
                end += 1
            elif (
                text[end] == " "
                and end > start
                and digits(text[end - 1])
                and numeric(text[start:end])
                and sum(digits(c) for c in text[start:end]) <= 19
                and end + 1 < len(text)
                and digits(text[end + 1])
            ):
                end += 1
            else:
                break
        token = text[start:end]
        if any(len(part) > 256 for part in token.split(" ")):
            raise ValueError("reference candidate overflow")
        if " " in token and numeric(token) and sum(digits(c) for c in token) > 19:
            raise ValueError("reference numeric bridge overflow")
        result.append("[REDACTED]" if sensitive(token) else token)
        start = end
    return "".join(result)
