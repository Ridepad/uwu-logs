const SEARCH_TYPES = {
  "flag": "Flag",
  "sGUID": "Source GUID",
  "tGUID": "Target GUID",
  "spellName": "Spell Name",
  "spellID": "Spell ID"
}
const submitButton = document.getElementById("submit-button");
const searchField = document.getElementById("db-search-field");


document.querySelectorAll('select').forEach(e => {
  for (let v in SEARCH_TYPES) {
    const _option = document.createElement('option');
    _option.setAttribute("value", v); 
    _option.innerHTML = SEARCH_TYPES[v];
    e.appendChild(_option);
  }
})

const responseField = document.getElementById("response-field");
const xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = () => {
  if (xhttp.readyState == 4 && xhttp.status == 200) {
    responseField.innerHTML = xhttp.response;
  }
}

submitButton.addEventListener('click', () => {
  const parsed = {};
  const articles = searchField.children
  for (let i=0; i<articles.length; i++) {
    const article = articles[i]
    const select = article.querySelector('.db-search-category')
    const input = article.querySelector('.db-search-input')
    parsed[select.value] = input.value;
  }
  const new_params = new URLSearchParams(parsed).toString();
  console.log(new_params);
  xhttp.open("POST", "/reports/{{ report_id }}/custom_search_post", true);
  xhttp.send(new_params)
  // loc.replace(`${loc.origin}${loc.pathname}?${new_params}`);
});