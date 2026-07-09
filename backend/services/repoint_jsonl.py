import argparse
import json
from pathlib import Path
 
 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="Path to the original JSONL manifest")
    parser.add_argument("--out", required=True, help="Path to write the repointed JSONL manifest")
    parser.add_argument("--old-dir", default="dataset/audio", help="Old audio folder substring to replace")
    parser.add_argument("--new-dir", default="dataset/audio_fixed", help="New audio folder to point to")
    parser.add_argument("--field", default="audio_filepath", help="JSON key holding the audio path")
    args = parser.parse_args()
 
    src_path = Path(args.src)
    out_path = Path(args.out)
 
    total, changed, missing_field = 0, 0, 0
 
    with open(src_path, "r", encoding="utf-8") as f_in, open(out_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            total += 1
            record = json.loads(line)
 
            if args.field not in record:
                missing_field += 1
                f_out.write(json.dumps(record) + "\n")
                continue
 
            old_path = record[args.field]
            if args.old_dir in old_path:
                new_path = old_path.replace(args.old_dir, args.new_dir)
                record[args.field] = new_path
                changed += 1
 
            f_out.write(json.dumps(record) + "\n")
 
    print(f"Total records     : {total}")
    print(f"Paths repointed   : {changed}")
    print(f"Missing '{args.field}' field: {missing_field}")
    print(f"Written to        : {out_path.resolve()}")
 
 
if __name__ == "__main__":
    main()
