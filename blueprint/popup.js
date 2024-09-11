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
        data = await fetchURLWithImageHandler(fetchURL, imageData);
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
  chrome.storage.sync.get(["userInfo"], (result) => {
    document.getElementById("name").value = result.userInfo.personalInfo.lastName + result.userInfo.personalInfo.firstName;
    document.getElementById("dateOfBirth").value = result.userInfo.personalInfo.dateOfBirth;
    document.getElementById("email").value = result.userInfo.personalInfo.email;
    document.getElementById("address").value = result.userInfo.personalInfo.address;
    document.getElementById("phoneNumber").value = result.userInfo.personalInfo.phoneNumber;
  });
}

// 크롬 스토리지 세팅하는 함수
function setChromeStorage(obj) {
  chrome.storage.sync.set({
    userInfo: obj.data,
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
    formData.append("file", imageData);

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
