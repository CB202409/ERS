from fastapi import WebSocket
from app.rag_chain import RAGChain
from app.pdf_utils import list_files_with_paths
from app.static_variables import Static_variables

source_list = list_files_with_paths(Static_variables.PDF_DIRECTORY_PATH)
rag_chain = RAGChain(source_list)

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            question = await websocket.receive_text()
            results = await rag_chain.process_question(question)
            for result in results:
                await websocket.send_json(result)
        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")
            break