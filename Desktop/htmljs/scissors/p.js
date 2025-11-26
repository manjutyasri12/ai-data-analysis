class User{
    constructor(name,email){
        this.name=name;
        this.email=email;
    }
    viewdata(){
        console.log("name:-",this.name);
         console.log("email:-",this.email);

    }
}
class admin extends User{
    constructor (name1,email1){
       super(name1,email1)


    }
editeddata(){
     console.log("name:-",this.name1);
         console.log("email:-",this.email1);


}
}
let u1=new User("manju","manjunath2@gmail.com");


u1.viewdata();
let a1=new admin("tarun","tarun@gmail.com");
a1.editeddata();


