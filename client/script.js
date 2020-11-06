

hashCode = function(s){
    return s.split("").reduce(function(a,b){a=((a<<5)-a)+b.charCodeAt(0);return a&a},0);              
}
window.onload = function() {
    function updateImage() {
        let now = new Date()
        fetch('http://192.168.1.2:8888/?ts='+ Math.round(now.getTime()))
        .then((response) => {
            return response.text();
        })
        .then((data) => {
            document.getElementById("img").src = "data:image/jpeg;base64," + data;
            
            //console.log('h:', hashCode(data))
        });
    }

    setInterval(updateImage, 50);
}