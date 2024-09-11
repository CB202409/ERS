document.addEventListener("DOMContentLoaded", () => {
  // 이미지 업로드 해 fetch 후 크롬 스토리지에 저장
  document
    .getElementById("fetchform1")
    .addEventListener("submit", async function (event) {
      event.preventDefault();
      // TODO: URL 확인 로직 필요
      fetchURL = event.target.fetchURL?.value;
      imageData = event.target.uploadImage?.files[0];
      if (fetchURL && imageData) {
        data = await fetchPostToJson(fetchURL, imageData);
        if (data) {
          console.log(data);
          setChromeStorage(data);
        }
      } else {
        alert("올바른 URL과 파일을 입력하쇼");
      }
    });

  // 이미지 등록 버튼 처리
  document.getElementById("uploadImage").addEventListener("change", (evt) => {
    alert("이미지 등록: " + evt.target.files[0].name);
    document.getElementById("uploadImageLabel").innerText = "등록 완료";
    document.getElementById("uploadImageLabel").className +=
      " btn-success disabled";
  });

  // 크롬 스토리지에 있는 내용을 현재 페이지에 내보내기
  document.getElementById("exportbtn1").addEventListener("click", function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        files: ["fillForm.js"],
      });
    });
  });
});


// 크롬 스토리지 세팅하는 함수
function setChromeStorage(obj) {
  chrome.storage.sync.set({
    userInfo: obj.data,
  });
  console.log("chrome storage saved!!!");
}

// 이미지와 함께 fetch
async function fetchPostToJson(fetchURL, imageData) {
  try {
    const formData = new FormData();
    if (imageData) {
      formData.append("file", imageData);
    }

    const response = await fetch(fetchURL, {
      method: "POST",
      body: formData,
    });
    const result = await response.json();
    alert("완료!");
    return result;
  } catch (error) {
    alert(error);
    console.log(error);
  }
}
