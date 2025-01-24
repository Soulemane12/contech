import os
from julep import Julep
from rdflib import Graph
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import time

# Load API key
load_dotenv(os.path.join(os.path.dirname(__file__), '../key', '.env'))

# Check if the API key is set
if not os.getenv("JULEP_API_KEY"):
    raise ValueError("JULEP_API_KEY environment variable is not set.")

# Initialize Julep client
client = Julep(api_key=os.getenv("JULEP_API_KEY"))

# Initialize Julep agent
try:
    agent = client.agents.create(
        name="PDF_RDF_Analyzer",
        model="gpt-4o",
        about="You analyze PDF documents and RDF data to answer questions."
    )
    print("Julep Agent created successfully.")
except Exception as e:
    print(f"Error creating Julep Agent: {str(e)}")
    agent = None



def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
        return ""


def query_rdf(graph, sparql_query):
    try:
        results = graph.query(sparql_query)
        return "\n".join([str(row) for row in results])
    except Exception as e:
        print(f"Error querying RDF graph: {e}")
        return ""


def generate_response_from_data(question, pdf_text, rdf_results):
    if not question:
        print("No question provided.")
        return ""

    if not pdf_text and not rdf_results:
        print("No data from PDFs or RDF.")
        return ""

    if not agent:
        print("Agent is not initialized.")
        return ""

    prompt = f"""
    You are an intelligent assistant that analyzes data from PDFs and RDFs.

    PDF Data:
    {pdf_text}

    RDF Data:
    {rdf_results}

    User Question:
    {question}

    Provide a clear and concise response.
    """

    try:
        task = client.tasks.create(
            agent_id=agent.id,
            name="PDF and RDF Question Answering",
            description="Analyze data from PDFs and RDF.",
            main=[
                {
                    "prompt": [
                        {"role": "system", "content": "You are a data assistant analyzing PDFs and RDFs."},
                        {"role": "user", "content": prompt}
                    ],
                    "return": {"result": "Answer to the user's question."}
                }
            ]
        )

        execution = client.executions.create(task_id=task.id, input={})
        while True:
            result = client.executions.get(execution.id)
            if result.status in ["succeeded", "failed"]:
                break
            print("Processing...")
            time.sleep(1)

        if result.status == "succeeded":
            return result.output.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            print(f"Task failed: {result.error}")
            return ""

    except Exception as e:
        print(f"Error generating response with Julep: {e}")
        return ""


if __name__ == "__main__":
    pdf_file = "data.pdf"
    rdf_file = "data.rdf"

    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found.")
        exit(1)

    if not os.path.exists(rdf_file):
        print(f"Error: RDF file '{rdf_file}' not found.")
        exit(1)

    pdf_data = extract_text_from_pdf(pdf_file)

    rdf_graph = Graph()
    try:
        rdf_graph.parse(rdf_file, format="xml")
        sparql_query = """
        SELECT ?subject ?predicate ?object
        WHERE { ?subject ?predicate ?object. }
        LIMIT 10
        """
        rdf_data = query_rdf(rdf_graph, sparql_query)
    except Exception as e:
        print(f"Error parsing RDF file: {e}")
        rdf_data = ""

    user_question = "What are the insights from the dataset?"
    response = generate_response_from_data(user_question, pdf_data, rdf_data)
    print("Chatbot Response:")
    print(response)
