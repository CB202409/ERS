document.addEventListener("DOMContentLoaded", () => {
  // 이미지 업로드 해 fetch 후 크롬 스토리지에 저장
  document
    .getElementById("fetchform1")
    .addEventListener("submit", async function (event) {
      event.preventDefault();
      // TODO: URL 확인 로직 필요
      fetchURL = event.target.fetchURL?.value;
      if (fetchURL) {
        data = await fetchURLWithImageHandler(fetchURL);

        console.log(data);
        setChromeStorage(data);
      } else {
        alert("올바른 URL을 입력하쇼");
      }
    });

  // 이미지 등록 버튼 처리
  document.getElementById("upload-image").addEventListener("change", (evt) => {
    alert("이미지 등록: " + evt.target.files[0].name);
    document.getElementById("upload-image-label").innerText = "등록 완료";
    document.getElementById("upload-image-label").className += " btn-success disabled";
  });

  // 크롬 스토리지에 있는 내용을 dummy-html에 내보내기
  document.getElementById("exportbtn1").addEventListener("click", function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        function: fillFormHandler,
      });
    });
  });
});

// TODO: 태그 역시 JSON에서 가져와야함
function fillFormHandler() {
  chrome.storage.sync.get(["name", "age", "gender", "address"], (result) => {
    document.getElementById("name").value = result.name;
    document.getElementById("age").value = result.age;
    document.getElementById("gender").value = result.gender;
    document.getElementById("address").value = result.address;
  });
}

// 크롬 스토리지 세팅하는 함수
function setChromeStorage(obj) {
  chrome.storage.sync.set({
    data: obj.data,
  });
  console.log("chrome storage saved!!!");
}

// post로 fetch만 하는 함수
// async function fetchURLHandler(fetchURL) {
//   try {
//     const response = await fetch(fetchURL, {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//     });
//     const result = await response.json();
//     alert("완료!");
//     return result;
//   } catch (error) {
//     alert(error);
//     console.log(error);
//   }
// }

// 이미지와 함께 fetch
async function fetchURLWithImageHandler(fetchURL, imageData) {
  try {
    const formData = new FormData();
    formData.append("image", imageData);

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
