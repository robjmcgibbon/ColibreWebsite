var active = false;

function update_sliders(x, y) {
  var width = $("#plot-container").width();
  var height = $("#plot-container").height();
  //var pos = $("#plot-container").position();
  var pos = $("#plot-container").offset();
  var pos_x = Math.max(0, Math.min(width, x - pos.left));
  var pos_y = Math.max(0, Math.min(height, y - pos.top));
  $("#horizontal-slider").css("left", `${pos_x-3}px`);
  $("#vertical-slider").css("top", `${pos_y-3}px`);
  $('.img2').css('width', `${pos_x}px`);
  $('.img3').css('height', `${pos_y}px`);
  $('.img4').css('width', `${pos_x}px`);
  $('.img4').css('height', `${pos_y}px`);
  $('.slider-button').css("left", `${pos_x-15}px`);
  $('.slider-button').css("top", `${pos_y-15}px`);
}
$("#plot-container").on("mousedown", (e) => {
  active = true;
  update_sliders(e.pageX, e.pageY);
});
$("#plot-container").on("mousemove", (e) => {
  if (active === true) {
    e = e || window.event;
    e.preventDefault();
    update_sliders(e.pageX, e.pageY);
  }
});
$("#plot-container").on("mouseup", (e) => {
  active = false;
});
$("#plot-container").on("touchstart", (e) => {
  active = true;
  update_sliders(e.pageX, e.pageY);
});
$("#plot-container").on("touchmove", (e) => {
  if (active === true) {
    e = e.changedTouches[0];
    update_sliders(e.pageX, e.pageY);
  }
});
$("#plot-container").on("touchend", (e) => {
  active = false;
});

function update_img_size() {
  var width = $("#plot-container").width();
  $('#plot-container').css('height', `${width}px`);
  $('.img').css('background-size', `${width}px ${width}px`);
}
update_img_size();
var pos = $('.slider-button').position();
$('.slider-button').css("left", `${pos.left-15}px`);
$('.slider-button').css("top", `${pos.top-15}px`);
$("#horizontal-slider").css("left", `${pos.left-3}px`);
$("#vertical-slider").css("top", `${pos.right-3}px`);

var sliders = null;
var active_slider = 0;
var num_sliders = 0;

function update_slider(){
  if(sliders == null){
    return;
  }
  var slider = sliders[active_slider];
  var caption = slider.label;
  $(".caption").html(`<p>${caption}</p>`);
  var images = slider.images;
  var nimg = Object.keys(images).length;
  var label_offset = 0;
  if(nimg == 2){
    label_offset = 2;
  }
  var iimg = 1;
  for(var label in images){
    var img = images[label];
    $(`.img${iimg}`).css('background-image', `url("${img}")`);
    $(`.img${iimg}`).css('display', 'block');
    /*$(`.label${label_offset+iimg}`).html(`<p>${label}</p>`);*/
    $(`.label${label_offset+iimg}`).html(`${label}`);
    $(`.label${label_offset+iimg}`).css('display', 'block');
    iimg++;
  }
  if(iimg == 3){
    for(;iimg <= 4; iimg++){
      $(`.img${iimg}`).css('display', 'none');
      $(`.label${iimg-label_offset}`).css('display', 'none');
    }
    $("#vertical-slider").css('display', 'none');
  } else {
    $("#vertical-slider").css('display', 'block');
  }
}

function previousSlider() {
  active_slider = (active_slider+num_sliders-1)%num_sliders;
  update_slider();
}

function nextSlider() {
  active_slider = (active_slider+1)%num_sliders;
  update_slider();
}

function selectSlider(num) {
  document.getElementById("link" + active_slider).className = "list-group-item"
  active_slider = num;
  document.getElementById("link" + num).className = "list-group-item active"
  update_slider();
}

$.getJSON("assets/images.json", function(data){
  sliders = data.sliders;
  num_sliders = sliders.length;
  update_slider();
});
