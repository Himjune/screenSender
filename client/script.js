

hashCode = function(s){
    return s.split("").reduce(function(a,b){a=((a<<5)-a)+b.charCodeAt(0);return a&a},0);              
}


let domain = document.URL;
console.log(domain);
domain = domain.split('/')[2]
console.log(domain);
domain = domain.split('/')
console.log(domain);
let link = 'http://'+domain+'/?ts='

window.onload = function() {
    function updateImage() {
        let now = new Date()
        fetch(link + Math.round(now.getTime()))
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