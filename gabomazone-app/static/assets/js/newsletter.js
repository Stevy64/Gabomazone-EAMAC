window.onload = function () {
    const formOne = document.querySelector(".selector-1");
    const formTwo = document.querySelector(".selector-2");

    const subscribeInputOne = document.getElementById("subscribe-input-1");
    const subscribeInputTwo = document.getElementById("subscribe-input-2");
    const csrf = document.getElementsByName('csrfmiddlewaretoken');

    const boxMessage = document.getElementById("alert-container");
    if(formOne){					
        formOne.addEventListener('submit', e =>{
                
                e.preventDefault();
                $.ajax({
                    type: "POST",            
                    url : "/letter/",
                    data: {
                        'csrfmiddlewaretoken': csrf[0].value ,
                        'value':subscribeInputOne.value,
                            },
                    success : function(response){
                            
                            boxMessage.classList.remove("not-visible")
                            boxMessage.innerHTML=`<div class="alert alert-${response.alert} alert-dismissible">	
                                                    <i class="fi-rs-${response.mark} message-icon"></i>
                                                    ${response.message}
                                                    <span class="btn-close" data-bs-dismiss="alert" aria-label="close"></span>
                                                </div>`
                            setTimeout(()=>{
                                boxMessage.classList.add("not-visible")
                                subscribeInputOne.value=""
                            },3000)
                            },
                    error : function(error){
                                
                                boxMessage.classList.remove("not-visible")
                                boxMessage.innerHTML=`<div class="alert alert-danger alert-dismissible">	
                                                    <i class="fi-rs-cross-circle message-icon"></i>
                                                    Oups... Une erreur est survenue !
                                                    <span class="btn-close" data-bs-dismiss="alert" aria-label="close"></span>
                                                </div>`
                            setTimeout(()=>{
                                boxMessage.classList.add("not-visible")
                                subscribeInputOne.value=""
                            },2000)
                            },


                })  
                    

            }) 
    }


    if(formTwo){					
        formTwo.addEventListener('submit', e =>{
                
                e.preventDefault();
                $.ajax({
                    type: "POST",            
                    url : "/letter/",
                    data: {
                        'csrfmiddlewaretoken': csrf[0].value ,
                        'value':subscribeInputTwo.value,
                            },
                    success : function(response){
                            
                            boxMessage.classList.remove("not-visible")
                            boxMessage.innerHTML=`<div class="alert alert-${response.alert} alert-dismissible">	
                                                    <i class="fi-rs-${response.mark} message-icon"></i>
                                                    ${response.message}
                                                    <span class="btn-close" data-bs-dismiss="alert" aria-label="close"></span>
                                                </div>`
                            setTimeout(()=>{
                                boxMessage.classList.add("not-visible")
                                subscribeInputTwo.value=""
                            },3000)
                            },
                    error : function(error){
                                
                                boxMessage.classList.remove("not-visible")
                                boxMessage.innerHTML=`<div class="alert alert-danger alert-dismissible">	
                                                    <i class="fi-rs-cross-circle message-icon"></i>
                                                    Oups... Une erreur est survenue !
                                                    <span class="btn-close" data-bs-dismiss="alert" aria-label="close"></span>
                                                </div>`
                            setTimeout(()=>{
                                boxMessage.classList.add("not-visible")
                                subscribeInputTwo.value=""
                            },2000)
                            },


                })  
                    

            }) 
    }
}    