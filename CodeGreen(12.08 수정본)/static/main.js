$(document).ready(function() {
    // 페이지가 로드되면 showHeart() 호출
    showHeart();
});

// 하트 상태를 확인하는 함수
function showHeart() {
    $.ajax({
        type: 'GET',
        url: '/show_heart/{{name}}/',  // 서버에 GET 요청
        data: {},
        success: function(response) {
            let my_heart = response['my_heart'];  // 서버로부터 받은 응답 데이터
            if (my_heart && my_heart['interested'] === 'Y') {
                // 사용자가 이미 "좋아요"를 눌렀다면, 하트를 빨간색으로
                $("#heart").css("color", "red");
                $("#heart").attr("onclick", "unlike()");  // "좋아요 취소" 함수 호출
            } else {
                // "좋아요"를 안 눌렀다면, 하트를 회색으로
                $("#heart").css("color", "grey");
                $("#heart").attr("onclick", "like()");  // "좋아요" 함수 호출
            }
        },
        error: function(request, status, error) {
            console.error("AJAX error:", error);  // 에러 발생 시 콘솔에 출력
        }
    });
}

// "좋아요" 클릭 시 처리 함수
function like() {
    $.ajax({
        type: 'POST',
        url: '/like/{{name}}/',  // 서버에 POST 요청 (좋아요 상태 저장)
        data: { interested: 'Y' },  // "좋아요" 상태 전달
        success: function(response) {
            alert(response['msg']);  // 서버에서 보내온 메시지를 표시
            window.location.reload();  // 페이지 새로고침
        },
        error: function(request, status, error) {
            console.error("AJAX error:", error);  // 에러 발생 시 콘솔에 출력
        }
    });
}

// "좋아요 취소" 클릭 시 처리 함수
function unlike() {
    $.ajax({
        type: 'POST',
        url: '/unlike/{{name}}/',  // 서버에 POST 요청 (좋아요 취소 상태 저장)
        data: { interested: 'N' },  // "좋아요 취소" 상태 전달
        success: function(response) {
            alert(response['msg']);  // 서버에서 보내온 메시지를 표시
            window.location.reload();  // 페이지 새로고침
        },
        error: function(request, status, error) {
            console.error("AJAX error:", error);  // 에러 발생 시 콘솔에 출력
        }
    });
}