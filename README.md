# HomeLex
고용노동법 관련 법률 자문과 계산이 필요한 사람들을 위한 법률 전문 AI 챗봇
## 목표
### Hallucination 정보를 사용자가 받지 않는 법률 서비스
- 법적 문제는 Hallucination의 발생 자체가 치명적이기 때문에, 답변의 정확도를 높임과 동시에 Hallucination이 발생할 수 밖에 없는 상황에서의 처리를 고려함
### 계산이 정확한 법률 서비스
- 법적으로 여러요소를 고려한 계산을 LLM을 이용해 정확하게 하기 위한 처리를 고려함
## 기술 스택
- React(with Vite)
- Python
  - Poetry
  - LangChain, LangSmith, LangGraph
  - FastAPI
- Pinecone
- Upstage Embedding Model
- SQLite
## 특징
### 서비스에 맞는 질문인 지를 확인하는 AGENT
- 불필요하게 Retrieve를 하여 지연시간을 늘리거나 리소스를 낭비하지 않기 위해 메인 동작 전, 질문을 판단하는 AGENT 배치
### RAG(검색증강생성)을 위한 Retriever
- PDFPlumber를 이용한 문서 load
- CharacterTextSplitter 방식으로 split
- Pinecone에 Dense vector, Sparse vector를 함께 저장
  - Dense vector: Upstage Embedding Model을 이용한 저장
  - Sparse vector: Kiwi 형태소 분석기를 통해 형태소 분할 후, 불용어 제거 한 뒤 BM25 알고리즘 기반으로 저장
### RAGAS를 이용한 하이퍼파라미터 미세조정
Chunk Size, Chunk Overlap, k, alpha 값을 조정하고, 정량적으로 테스트하며 성능이 좋은 하이퍼파라미터를 사용
### 질문의 내용이 문서에 기반한 것인 지를 확인하는 AGENT
- LLM이 임의의 판단으로 대답을 한 것인지를 확인해 Hallucination이 생긴 대답은 쿼리를 재작성하도록 함.
- 만약 Hallucination이 반복된다면, 문서에서 내용을 찾을 수 없음을 나타내고 종료.
## FlowChart
![image](https://github.com/user-attachments/assets/ebc79c76-7bea-4cf8-9793-f780bd0a8c66)



## 서비스 핵심 기능
- 법률 요약 정보 제공, 필요 시, '더 궁금해요'버튼을 통한 상세 정보 제공
- 자주묻는 질문
- 실업급여, 최저임금, 퇴직금 계산


### 동작 페이지
<img src="https://github.com/user-attachments/assets/d2002187-1c30-4482-8fd3-41ba73f6b26b" width="50%"/>
<br/>
<img src="https://github.com/user-attachments/assets/09425ec8-29fa-4203-ac76-7f1883be0ee9" width="50%"/>
<br/>
<img src="https://github.com/user-attachments/assets/1a8399cd-3e8e-4cfa-9391-47525c1ef8bc" width="50%"/>
<br/>
<img src="https://github.com/user-attachments/assets/1a8399cd-3e8e-4cfa-9391-47525c1ef8bc" width="50%"/>
<br/>
<img src="https://github.com/user-attachments/assets/c9fb7628-15cb-4170-898c-75c09a1cd017" width="50%"/>
