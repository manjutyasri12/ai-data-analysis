

function displayName(){
    const name1=document.getElementById("name");
   const userName=name1.value;
    alert("hello1 !"+userName+"!");


}
let sub1=document.getElementById("sub1");
sub1.addEventListener("click",()=>{
    displayName();
});
let stid=document.getElementById("stone");
stid.addEventListener("click",()=>{
    console.log('clicked');
})