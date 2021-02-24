var updateBtns = document.getElementsByClassName('update-cart')

for (var i = 0; i<updateBtns.length; i++){
    updateBtns[i].addEventListener('click', function(){
        var productId = this.dataset.product
        var action = this.dataset.action
        console.log('productId:',productId, 'action:',action)

        console.log('User:', user)

        if (user === 'AnonymousUser'){
            console.log('user not logged in')
        }
        else{
            updateUserOrder(productId,action)
        }

    })
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  async function delayedGreeting() {
    await sleep(10000000000);
    await sleep(30000);
  }
  
  delayedGreeting();



function updateUserOrder(productId,action){
    console.log('user logged in, sending data...')
    console.log(productId,action);

    var url = '/update_item/'

    fetch(url,{
        method:'POST',
        headers:{
            'Content-Type':'application/json',
            'X-CSRFToken':csrftoken,
        },
        body:JSON.stringify({'productId':productId, 'action':action})
    })

    

    .then((response) => {
        delayedGreeting();
        return response.json()
    })
    
    .then((data) => {
        console.log('data:', data)
        location.reload()
    })


}