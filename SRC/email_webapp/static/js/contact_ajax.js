const searchField = document.querySelector("#searchField");
const contactResult = document.querySelector(".contact_ajax_result");
const listAjax = document.querySelector(".list_ajax");
contactResult.style.display = "none";

const listDisplay = document.querySelector(".list_div");
const result = document.querySelector(".result");


searchField.addEventListener('keyup', function (e) {

    const searchValue = e.target.value;
    if (searchValue.trim().length > 0) {
        console.log('searchValue', searchValue);
        listAjax.innerHTML = " "
        fetch("/accounts/search-contact/", {
            body: JSON.stringify({searchText: searchValue}),
            method: "POST",
        })
            .then((res) => res.json())
            .then((data) => {
                console.log("data", data);

                listDisplay.style.display = "none";
                contactResult.style.display = "block";

                if (data.length === 0) {
                    contactResult.innerHTML = "No result!";
                } else {
                    contactResult.innerHTML = " "
                    data.forEach((item) => {
                        contactResult.style.display = "none"
                        listAjax.innerHTML +=

                            `<li>
                                        <a href="/accounts/contact-detail/" onclick="location.href=this.href+${item.id};return false;">
                                          ${item.name} : ${item.email}
                                        </a>
                            </li>`

                    })
                }

            });

    } else {
        result.style.display = "none";
        contactResult.style.display = "none";
        listDisplay.style.display = "block";
    }

})