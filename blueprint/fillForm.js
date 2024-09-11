// 현재 페이지에서 Tag 정보 가져와 생성형AI에게 정리를 맡겨 받는 함수
async function autoFillFormHandler() {
  // console.log(pageTagInfo);
  // keys = ["userInfo"];
  
  /* 현재 페이지에서 input 태그를 다 가져와 inputTagsSum에 텍스트로 저장 */
  const inputTags = document.querySelectorAll("input");
  let inputTagsSum = "";
  inputTags.forEach((form) => {
    inputTagsSum += form.outerHTML;
  });
  
  /* inputTagsSum을 서버로 전송(Gemini) */
  parserURL = "http://127.0.0.1:8001/";
  pageTagInfo = await fetchPostToJson(parserURL, inputTagsSum);
  console.log(pageTagInfo);

  /* 크롬 스토리지에서 데이터 가져오기 */
  keys = ["userInfo"];
  const userInfo = await new Promise((resolve, reject) => {
    chrome.storage.sync.get(keys, (result) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(result.userInfo);
      }
    });
  });
  console.log(userInfo);


  /* userInfo값과 pageTagInfo값을 이용, 현재 페이지 채우기 */
  for (const [key, cssSelector] of Object.entries(pageTagInfo.pageInfo.personalInfo)) {
    if (cssSelector) {
      const inputElement = document.querySelector(cssSelector);
      if (inputElement) {
        inputElement.value = userInfo.personalInfo[key] || '';
      }
    }
  }  
}

async function fetchPostToJson(fetchURL, inputString) {
  try {
    const sendData = { param1: inputString };

    const response = await fetch(fetchURL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(sendData)
    });
    const result = await response.json();
    alert("완료!");
    return result;
  } catch (error) {
    alert(error);
    console.log(error);
  }
}

autoFillFormHandler();