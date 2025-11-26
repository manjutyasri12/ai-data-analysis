let boxes=document.querySelectorAll(".box");
let ib=document.querySelectorAll(".mb");
let wmsg=document.querySelector("#wmsg");

let p1=true;
let iswin;
let winner=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
const winnerm=()=>{
    for(let v of winner){
        ply1=ib[v[0]].innerText;
    ply2=ib[v[1]].innerText;
    ply3=ib[v[2]].innerText;
    if((ply1!==""&&ply1!==""&&ply1!=="")&&(ply1===ply2&&ply3===ply2)){
        console.log("winner");
        //  show(ply1);
        for(let m of ib){
            m.disabled=true;
            
        }
       
        
        wmsg.innerText=`congrats ${ply1}wins`;
        wmsg.classList.remove("hide");
       
        
    }
    
}
}
let resetbtn=document.querySelector("#reset");
resetbtn.addEventListener("click",()=>{
    enable();


});
let ng=document.querySelector("#ng");
ng.addEventListener("click",()=>{
    enable();


});
const enable=()=>{
    for(let n of ib){
        n.innerText="";
        n.disabled=false;
    }
}
const show=(a)=>{
wmsg.innerText=`congrats ${a}wins`;
        wmsg.classList.remove("hide");}

ib.forEach((b)=>{
    b.addEventListener("click",()=>{
        if(p1===true){
           console.log("clicked by player 1");
           b.innerText="X";
           p1=false;
        }
        else{
            console.log("clicked by player 2");
             b.innerText="O";
           p1=true;

        }
        b.disabled=true;
        winnerm();
       

        
    })
    


});

