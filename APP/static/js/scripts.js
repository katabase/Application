/*****************************************************************************/

// CHANGE BEHAVIOUR OF #pills-manuscript-tab and #pills-sell-tab
// defining variables
const manuscript = document.querySelector("#pills-manuscript-tab");
const sell = document.querySelector("#pills-sell-tab");
 if (manuscript != null && sell != null){
  // base behaviour of the buttons
  function baseClicks() {
    sell.setAttribute("style", "border: 1px solid; border-color: var(--custom-main1); background-color: var(--custom-main2); color: var(--custom-cream);");
    manuscript.setAttribute("style", "border: 1px solid; border-color: var(--custom-main1); background-color: var(--custom-cream); color: var(--custom-main2);");
  };
  window.onload = baseClicks();
   // when clicking on "View by manuscript"
  function clickManuscript() {
    sell.setAttribute("style", "border: 1px solid; border-color: var(--custom-main1); background-color: var(--custom-cream); color: var(--custom-main2);");
    manuscript.setAttribute("style", "background-color: var(--custom-main2); color: var(--custom-cream);");
  };
   // when clicking on "View by sale"
  function clickSell() {
    manuscript.setAttribute("style", "border: 1px solid; border-color: var(--custom-main1); background-color: var(--custom-cream); color: var(--custom-main2);");
    sell.setAttribute("style", "background-color: var(--custom-main2); color: var(--custom-cream);");
  };
};

/*****************************************************************************/

// CHANGE FIGURE ON INDEX PAGE

// defining variables
const dwn = $("#dwn");  // dropdown
const dft = $(dwn).children("[value=1]");  // default value: "Total sales per year"
const ifr = $("#fig iframe");  // iframe

// if the button exists (if we are on the index page), trigger a javascript event: when the
// dropdown changes (when another option is selected), load the proper plotly figure
if (dwn != null) {
  // when the document is loaded, write a function that is triggered
  // when the selected dropdown item changes
  $(document).ready(function() {
     // set dropdown value to default
    $(dwn).val("1");
     $(dwn).change(function() {
      var selected = $(dwn).children("option").filter(":selected").val();   // currently selected option's @value
      var url = new URL(window.location.origin);  // root of the website's url
      var dest = url.href + "fig/IDX_" + selected;  // url pointing to the iframe selected in the dropdown
      // update the iframe element with the proper url
      $(ifr).attr("src", dest);
    });
  });
};

/*****************************************************************************/

// API: CODE COLOURING + ASYNC REQUESTS TO LIVE TEST THE API

$(document).ready(function(){
    /*
      if we're on the KatAPI page, add event listeners
      and colour the code
    */
    sendApi = $("#sendApi");
    if ($(sendApi) != null){
        $("#sendApi").click(function(){
            launchRequest();
        });
        document.querySelectorAll('pre code').forEach((el) => {
          hljs.highlightElement(el);
        });
    };
});

async function launchRequest() {
  /*
    launch an API request from the url inputted by the user
    on the KatAPI page
  */

  // prepare the request
  const url = new URL(window.location.href);
  const domain = url.origin;  // katabase.huma-num.fr

  try {
    // parse user input as JSON. if this input is invalid, then catch(e) is executed;
    // else, launch an async ajax request and add its content to $("#apiOut").
    let input = $("#apiUrl").val().replaceAll("'", '"');
    //let input = i.replace("'", '"');  // replace() to process the quotes into json compliant ones
    let params = JSON.parse(input);
    let request = new URL(`${domain}/katapi?`);  // complete url of the api's request

    // launch async ajax request and add results to $("apiOut");
    // to do so, parse the response as the string representation
    // of a json or of an XML.
    // if the http status code is not 200, an error is thrown and the
    // catch block is executed.
    response = await ajaxApi(request, params);
    if (response instanceof XMLDocument) {
      $("#apiOut").text(response.scrollingElement.outerHTML);
    } else {
      $("#apiOut").text(JSON.stringify(response, null, 4));
    };
    colorApiOut();

  } catch(e) {
    console.log(e);
    if (e instanceof SyntaxError) {
      // SyntaxError = Json parsing output
      $("#apiOut").text(
        "Your input is not a valid JSON. Please correct it and try again."
        + "\nHere are some things you might have missed:"
        + "\nAre your key-value couples separated by commas?"
        + "\nAre your research parameters enclosed inside curly brackets?"
        + "\nHere are some valid jsons:"
        + '\n{"format": "json", "level": "itm", "name": "sevigne"}'
        + '\n{"name": "sevigne", "level": "itm"}'
        + '\n{"id": "CAT_000352", "level": "cat_stat", "format": "tei"}'
      );

    } else if (e.status == 422 || e.status == 500) {
      // invalid user input or server error: see if it's an xml or json
      // response, parse it and send it back to the user.
      if (e.responseJSON) {
        $("#apiOut").text(JSON.stringify(e.responseJSON, null, 4));
      } else {
        $("#apiOut").text(e.responseText);
      };
      colorApiOut();

    };
  };
};

function ajaxApi(request, data) {
  /*
    launch the actual query through an ajax request
    :param request: the request url
    :param data: the request parameters provided by the user
    :return: the response
  */
  return $.ajax({
    type: "GET",
    url: request,
    data: data,
    error: function(response, status, error){
      // return response.responseText;
    },
    success: function(response){
      // return response;
    }
  });
}

function colorApiOut() {
  /*
    color the code returned by ajax
  */
  let apicode = document.querySelector("#apiOut");
  hljs.highlightElement(apicode);
}