import sys
import subprocess

def copy_to_clipboard(filename):
    try:
        with open(filename, "r") as file:
            content = file.read()

        # Use xsel since xclip is missing
        process = subprocess.Popen("xsel --clipboard --input", stdin=subprocess.PIPE, shell=True)
        process.communicate(input=content.encode("utf-8"))

        print(f"✅ Successfully copied {filename} to clipboard!")

    except Exception as e:
        print(f"❌ Error: {e}")

if len(sys.argv) < 2:
    print("Usage: python copy_to_clipboard.py <filename>")
else:
    copy_to_clipboard(sys.argv[1])

