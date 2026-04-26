function sendMessage(){
    let input = document.getElementById("user-input");
    let msg = input.value;

    if(msg.trim()==="") return;

    let box = document.getElementById("chat-box");

    box.innerHTML += `
    <div class="message user">
        <div class="bubble">${msg}</div>
        <div class="avatar">U</div>
    </div>`;

    fetch("/get",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({message:msg})
    })
    .then(res=>res.json())
    .then(data=>{
        box.innerHTML += `
        <div class="message bot">
            <div class="avatar">B</div>
            <div class="bubble">${data.reply}</div>
        </div>`;
        box.scrollTop = box.scrollHeight;
    });

    input.value="";
}