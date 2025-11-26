const http = require('http');

const hostname = '127.0.0.1';
const port = 5500;

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Hello World');
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});

// let string="manju";
// function vowel(string){
//     string.toLowerCase();
//     let n=string.length;
//     let count=0;
//     for(let val of string){
        
//     while(val=='a'||val=='e'||val=='i'||val=='o'||val=='u'){

//         count++;
//     }
//     }
//     console.log(count);
// }
// vowel(string);
// console.log("hiii");

