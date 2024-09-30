window.addEventListener("scroll", function() {
    const maxHeight = document.body.scrollHeight - window.innerHeight;
    var position = (window.scrollY * 100) / maxHeight;
//    position = Math.round((position + Number.EPSILON) * 10) / 10;
    position = position.toFixed(1);
    document.getElementById("scroll_pos").textContent=position+"%";
});
