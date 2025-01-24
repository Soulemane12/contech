import os
from dotenv import load_dotenv

load_dotenv(".env")
print(os.getenv("JULEP_API_KEY"))
