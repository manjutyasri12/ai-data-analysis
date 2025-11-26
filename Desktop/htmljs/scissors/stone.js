let stoneButton=document.querySelector("#stid");
let paperButton=document.querySelector("#pid");
let scissorButton=document.querySelector("#scid");
let ps=document.querySelector("#ps");
let cs=document.querySelector("#cs");
let wmsg=document.getElementById("winmsg");
let ng=document.getElementById("ng");
let ch=document.getElementById("ch");
let player,computerscore=0,playerscore=0;
ng.addEventListener("click",()=>{
    computerscore=0;
    playerscore=0;
    cs.innerText="computer score:-"+computerscore;
    ps.innerText="player score:-"+playerscore;
    wmsg.innerText="new game start";



})



stoneButton.addEventListener("click",()=>{
    console.log("stone clicked");
    player="st";
    comp(player);

});
paperButton.addEventListener("click",()=>{
    console.log("paper clicked");
    player="pa";
    comp(player);
    

});
scissorButton.addEventListener("click",()=>{
    console.log("scissors clicked");
    player="sc";
    comp(player);

});
function comp(player){
const choice=["st","pa","sc"];
const randomnumber=Math.floor(Math.random()*choice.length);
const answer=choice[randomnumber];
console.log(answer);
check(answer,player);


}
function check(answer,player){
    if(answer===player){
        console.log("tie");
         wmsg.innerText="it s adraw!!";
         if(answer==="st")
{
     ch.innerText="computer choice is:-stone";

}
   if(answer==="sc")
{
     ch.innerText="computer choice is:-scissors";

}
   if(answer==="pa")
{
     ch.innerText="computer choice is:-paper";

}
    }
    // stone
    else if(answer==="st"){
       
        if( player==="sc")
        {
            
            console.log("computer wins");
            wmsg.innerText="computer wins ";
             ch.innerText="computer choice is:-stone";
            computerscore+=1;
           
        }
        else{
             console.log("player wins");
              wmsg.innerText="player wins";
               ch.innerText="computer choice is:-stone";
            playerscore+=1;

        }
         } 
        //  paper 
        else if(answer==="pa"){
            
        if( player==="st")
        {
            console.log("computer wins");
             wmsg.innerText="computer wins";
             ch.innerText="computer choice is:-paper";
            computerscore+=1;
            
        }
        else{
             console.log("player wins");
              wmsg.innerText="player wins";
               ch.innerText="computer choice is:-paper";
            playerscore+=1;

        }
         } 
        //  scissors
        else if(answer==="sc"){
           
        if( player==="pa")
        {
            console.log("computer wins");
             wmsg.innerText="computer wins";
              ch.innerText="computer choice is:-scissors";
            computerscore+=1;
            
        }
        else{
             console.log("player wins");
              wmsg.innerText="player wins";
               ch.innerText="computer choice is:-scissors";
            playerscore+=1;

        }
         } 
          cs.innerText="computer score="+computerscore;
           ps.innerText="player score="+playerscore;

            
         console.log("plyayerscore ;-",playerscore);
         console.log("computerscore:-",computerscore);

       
}

