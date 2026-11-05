from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_transform import source_rows

output = Path("data/Online Retail.xlsx")
output.parent.mkdir(exist_ok=True)
source_rows().to_excel(output, index=False)
print(f"Wrote {output}")
