// When the user scrolls down 170px from the top of the document, resize the navbar
window.onscroll = function() {scrollFunction()};

function scrollFunction() {
  if (document.body.scrollTop > 170 || document.documentElement.scrollTop > 170) {
    document.getElementById("navbar").style.background = "black";
  } else {
    document.getElementById("navbar").style.background = "transparent";
  }
}

// the buttons that open and close sections
function toggle(id) {
  var state = document.getElementById(id).style.display;
  if (state == 'block') {
    document.getElementById(id).style.display = 'none';
  } else {
    document.getElementById(id).style.display = 'block';
  }
} 

// A normal toggle
function tbtoggle(id, button) {
  var state = document.getElementById(id).style.display;
  if (state == 'none') {
    document.getElementById(id).style.display = '';
    document.getElementById(button).innerHTML = '-';
  } else {
    document.getElementById(id).style.display = 'none';
    document.getElementById(button).innerHTML = '+';
  }
} 

// A set toggle
function settoggle(set, button, close) {
  console.log("function start", set, button, close);
  const collection = document.getElementsByClassName(set);
  const collection2 = document.getElementsByClassName(close);
  var state1 = document.getElementById(button).innerHTML;

  if (state1 == '-') {
    document.getElementById(button).innerHTML = '+';
    for (let i = 0; i < collection2.length; i++) {
      collection2[i].style.display = 'none';
      const buttonset = collection2[i].getElementsByTagName("button");
      if (buttonset.length > 0) {
        for (let b = 0; b < buttonset.length; b++) {
          buttonset[b].innerHTML = '+';
        }
      }
    }
  } else {
    for (let i = 0; i < collection.length; i++) {
      collection[i].style.display = '';
      document.getElementById(button).innerHTML = '-';      
    }
  }
}

// The map toggle
function maptoggle(id, button) {
  var state = document.getElementById(id).style.display;
  if (state == 'none') {
    document.getElementById(id).style.display = '';
    document.getElementById(button).innerHTML = '-';
    map.invalidateSize();
  } else {
    document.getElementById(id).style.display = 'none';
    document.getElementById(button).innerHTML = '+';
  }
} 

// A toggle with ajax call for RDF 
function tbtoggle2(id, button) {
  var state = document.getElementById(id).style.display;
  if (state == 'none') {
    document.body.style.cursor = "wait";
    var rdfaddress = document.getElementById('rdfajax').textContent;
    fetch(rdfaddress, {
        headers:{
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
      document.body.style.cursor = "default";
      document.getElementById(id).style.display = '';
      document.getElementById(button).innerHTML = '-';
      document.getElementById('rdfelement').innerText = data.rdftext;
    });
  } else {
    document.getElementById(id).style.display = 'none';
    document.getElementById(button).innerHTML = '+';
  }
}

// Handling the modal images
function image(id) {
  var modal = document.getElementById('myModal' + id);
  var captionText = document.getElementById('caption' + id);
  var imgElement = document.getElementById('modalimagebase' + id);

  if (modal && imgElement) {
    modal.style.display = "block";
    if (captionText) {
      captionText.innerHTML = imgElement.alt;
    }
  }
}

function modalclose(id) {
  var modal2 = document.getElementById('myModal' + id);
  if (modal2) modal2.style.display = "none";
}

// Alternate image handler for items with multiple images
function image2(id, phrase) {
  var modal = document.getElementById('myModal' + phrase + id);
  var captionText = document.getElementById('caption' + phrase + id);
  var imgElement = document.getElementById('modalimagebase' + phrase + id);

  if (modal && imgElement) {
    modal.style.display = "block";
    if (captionText) {
      captionText.innerHTML = imgElement.alt;
    }
  }
}

function modalclose2(id, phrase) {
  var modal2 = document.getElementById('myModal' + phrase + id);
  if (modal2) modal2.style.display = "none";
}

function serieslistupdate() {
  var statusrepository = document.getElementById('id_repository').value;

  if (statusrepository === "") {
    if (document.getElementById('series_label')) {
      document.getElementById('series_label').style.opacity = "0.6";
    }
  } else {
    var seriesoptions = document.getElementById('id_series').options;
    for (var j = 0; j < seriesoptions.length; j++) {
      seriesoptions[j].hidden = true;
      var seriesValue = seriesoptions[j].value;
      
      for (var key in series_data) {
        if (series_data[key].pk == seriesValue) {
          if (Number(series_data[key].fields.fk_repository) == statusrepository) {
            seriesoptions[j].hidden = false;
          }
        }
      }
    }             
  }
}
