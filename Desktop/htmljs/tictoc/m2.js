let mb=document.querySelectorAll(".mb");
let resetbtn=document.querySelector("#reset");
let box=document.querySelectorAll(".box");
let msgc=document.querySelector(".msgc");
let newbtn=document.querySelector("#ng");
let wmsg=document.querySelector("#wmsg");
let winner=[
     [0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]
]
let p1=true;

mb.forEach((b)=>{
     b.addEventListener("click",()=>{
          if(p1){
                console.log("clicked 1");
               b.innerText='x';
               p1=false;
          }
          else{
                console.log("clicked 2");
                b.innerText='o';
               p1=true;
               
          }
          b.disabled=true;
checkwinner();
let isWinner=false;

     
          

     })

}
     
);
const checkwinner=()=>{
     for(let pattern of winner){
      let position1=mb[pattern[0]].innerText;
       let position2=mb[pattern[1]].innerText;
        let position3=mb[pattern[2]].innerText;
          
        if(position1 !== "" && position2 !== "" && position3 !== "" ){
           if(position1 === position2 && position2 === position3){
            console.log("Winner", position1);
            show(position1);
             disablebox();
             isWinner=true;
           
        }   
        
     }
           }
//     if(position1 !== "" && position2 !== "" && position3 !== "" &&
//            position1 !== position2 && position2 !== position3){
//            wmsg.innerText="draw match,play one more time";
          
     
//            }
}
const disablebox=()=>{
     for(let b of mb){
     b.disabled=true;
     }
}
newbtn.addEventListener("click",()=>{
     enablebox();
     p1=false;
     for(let b of mb){
          b.innerText="";
     }
     wmsg.classList.add("hide");
})
resetbtn.addEventListener("click",()=>{
     enablebox();
      for(let b of mb){
          b.innerText="";
     }
     p1=true;
 wmsg.classList.add("hide");
})
const enablebox=()=>{
     for(let b of mb){
     b.disabled=false;
     }
}
const show=(a)=>{
     wmsg.innerText=`winner ${a},cograts`;
     wmsg.classList.remove("hide");
     
 
}
isWinner()