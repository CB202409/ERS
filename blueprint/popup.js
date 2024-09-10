document.addEventListener("DOMContentLoaded", () => {
  // JSON 읽어와 객체로 저장

  document
    .getElementById("fetchform1")
    .addEventListener("submit", async function (event) {
      event.preventDefault();
      // TODO: URL 확인 로직 필요
      fetchURL = event.target.fetchURL?.value;
      if (fetchURL) {
        data = await fetchURLHandler(fetchURL);

        console.log(data);
        setChromeStorage(data);
      } else {
        alert("URL을 입력해주세요");
      }
    });


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
    name: obj.name,
    age: obj.age,
    gender: obj.gender,
    address: obj.address,
  });
  console.log("chrome storage saved!!!");
}

// 일단은 FASTAPI를 이용한 더미 JSON으로 진행. 바꿔야함!
async function fetchURLHandler(fetchURL) {
  try {
    const response = await fetch(fetchURL, {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
      }
    });
    const result = await response.json();
    alert("완료!");
    return result;
  } catch (error) {
    alert(error);
    console.log(error);
  }
}
