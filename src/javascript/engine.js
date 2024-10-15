var canvas = document.getElementById("lightcone_img");
var ctx = canvas.getContext('2d');
var imageData = ctx.createImageData(resolution, resolution / 2);
var cbarData = ctx.createImageData(20, resolution / 2);
var logoData = ctx.createImageData(64, 64); /* 4 channels, RGBA */

$("#zslider").slider({
  range: true,
  min: global_zimin,
  max: global_zimax,
  values: [global_zimin, global_zimax],
  stop: function(event, ui) {
    var imin = $("#zslider").slider("values", 0);
    var imax = $("#zslider").slider("values", 1);
    if (imin == imax) {
      if (ui.handleIndex == 0) {
        $("#zslider").slider("values", 0, imax - 1);
      } else {
        $("#zslider").slider("values", 1, imin + 1);
      }
    }
    imin = $("#zslider").slider("values", 0);
    imax = $("#zslider").slider("values", 1);
    var zmin = get_zlabel(imin);
    var zmax = get_zlabel(imax);
    /*$("#zrange").val(zmin.toFixed(2) + " - " + zmax.toFixed(2));*/
    $("#zrange").val("[" + zmin.toFixed(2) + "," + zmax.toFixed(2) + "]");
    update_qrange();
    update_img();
  },
  slide: function(event, ui) {
    var imin = (ui.handleIndex == 0) ? ui.value : $("#zslider").slider(
      "values", 0);
    var imax = (ui.handleIndex == 1) ? ui.value : $("#zslider").slider(
      "values", 1);
      var zmin = get_zlabel(imin);
      var zmax = get_zlabel(imax);
    /*$("#zrange").val(zmin.toFixed(2) + " - " + zmax.toFixed(2));*/
    $("#zrange").val("[" + zmin.toFixed(2) + "," + zmax.toFixed(2) + "]");
  }
});
$("#zrange").val("[" + get_zlabel(global_zimin).toFixed(2) + "," + 
  get_zlabel(global_zimax).toFixed(2) + "]");
$("#qslider").slider({
  range: true,
  min: global_qmin,
  max: global_qmax,
  step: (global_qmax - global_qmin) / 100,
  values: [global_qmin_start, global_qmax],
  stop: function(event, ui) {
    var imin = $("#qslider").slider("values", 0);
    var imax = $("#qslider").slider("values", 1);
    if (imin == imax) {
      if (ui.handleIndex == 0) {
        $("#qslider").slider("values", 0, imax - 0.1);
      } else {
        $("#qslider").slider("values", 1, imin + 0.1);
      }
    }
    imin = $("#qslider").slider("values", 0);
    imax = $("#qslider").slider("values", 1);
    /*$("#CYrange").val(imin.toFixed(2) + " - " + imax.toFixed(2));*/
    $("#qrange").val("[" + imin.toFixed(2) + "," + imax.toFixed(2) + "]");
    update_img();
  },
  slide: function(event, ui) {
    var imin = (ui.handleIndex == 0) ? ui.value : $("#qslider").slider(
      "values", 0);
    var imax = (ui.handleIndex == 1) ? ui.value : $("#qslider").slider(
      "values", 1);
    /*$("#CYrange").val(imin.toFixed(2) + " - " + imax.toFixed(2));*/
    $("#qrange").val("[" + imin.toFixed(2) + "," + imax.toFixed(2) + "]");
  }
});
/*$("#CYrange").val(global_CYmin.toFixed(2) + " - " + global_CYmax.toFixed(2));*/
$("#qrange").val("[" + global_qmin_start.toFixed(2) + "," + global_qmax.toFixed(2) + "]");

function get_zlabel(index) {
  return (index <= zdiffswitch) ? index * zdiff : zdiffswitch * zdiff + (index - zdiffswitch) * zdiff2;
}

function update_qrange() {
  var imin = $("#zslider").slider("values", 0);
  var imax = $("#zslider").slider("values", 1);
  var newqmin = global_qmax;
  var newqmax = 0.0;
  for (let imap = imin; imap<imax; imap++) {
    newqmin = (q_map_minmax[imap][0] < newqmin) ? q_map_minmax[imap][0] : newqmin;
    newqmax += Math.pow(10., q_map_minmax[imap][1]);
  }
  newqmax = Math.min(Math.log10(newqmax), global_qmax);
  imin = $("#qslider").slider("values", 0);
  imax = $("#qslider").slider("values", 1);
  $("#qslider").slider("option", "min", newqmin);
  $("#qslider").slider("option", "max", newqmax);
  $("#qslider").slider("values", 0, Math.max(imin, newqmin));
  $("#qslider").slider("values", 1, Math.min(imax, newqmax));
  imin = $("#qslider").slider("values", 0);
  imax = $("#qslider").slider("values", 1);
  if ((imax - imin) < 0.1) { //I'd rather compare to step and set them "step" apart, but I can't get step...
    imin = imax - 0.1
    $("#qslider").slider("values", 0, imin);
  }
  $("#qrange").val("[" + imin.toFixed(2) + "," + imax.toFixed(2) + "]");
}

function update_img() {
  if (!imgcube) {
    return;
  }
  var imin = $("#zslider").slider("values", 0);
  var imax = $("#zslider").slider("values", 1);
  var qmin = $("#qslider").slider("values", 0);
  var qmax = $("#qslider").slider("values", 1);
  var img_map = new Float32Array(resolution * resolution / 2);
  var val;
  for (let imap = imin; imap < imax; imap++) {
    for (let i = 0; i < resolution * resolution / 2; i++) {
      val = imgcube[imap * resolution * resolution / 2 + i];
      if (!Number.isNaN(val)) { //otherwise a single NaN overwrites valid values, even though a NaN inside the ellipse is just a 0 value
        img_map[i] += Math.pow(10., val);
      }
    }
  }
  //Now only set NaNs outside the ellipse
  for (let i = 0; i < imgmask.length; i++) {
    img_map[imgmask[i]] = Number.NaN;
  }
  for (let ix = 0; ix < resolution / 2; ix++) {
    for (let iy = 0; iy < resolution; iy++) {
      var i = ix * resolution + iy;
      if (!Number.isNaN(img_map[i])) {
        var x = (Math.log10(img_map[i]) - qmin) / (qmax - qmin);
        //var x = (img_map[i] - CYmin) / (CYmax - CYmin);
        x = (x < 0.) ? 0. : x;
        x = (x > 0.9999) ? 0.9999 : x;
        x *= magma_data.length;
        var idx = Math.floor(x);
        var dx = x - idx;
        if (idx < magma_data.length - 1) {
          imageData.data[4 * i] = 255 * (magma_data[idx][0] * (1. - dx) +
            magma_data[idx + 1][0] * dx);
          imageData.data[4 * i + 1] = 255 * (magma_data[idx][1] * (1. - dx) +
            magma_data[idx + 1][1] * dx);
          imageData.data[4 * i + 2] = 255 * (magma_data[idx][2] * (1. - dx) +
            magma_data[idx + 1][2] * dx);
        } else {
          imageData.data[4 * i] = 255 * magma_data[idx][0];
          imageData.data[4 * i + 1] = 255 * magma_data[idx][1];
          imageData.data[4 * i + 2] = 255 * magma_data[idx][2];
        }
        imageData.data[4 * i + 3] = 255;
      }
    }
  }
  for (let iy = 0; iy < resolution / 2; iy++) {
    var color = [0, 0, 0, 255];
    var x = (resolution / 2 - 1 - iy) * 2. / resolution;
    x *= magma_data.length;
    var idx = Math.floor(x);
    var dx = x - idx;
    if (idx < magma_data.length - 1) {
      color[0] = 255 * (magma_data[idx][0] * (1. - dx) + magma_data[idx + 1][
        0
      ] * dx);
      color[1] = 255 * (magma_data[idx][1] * (1. - dx) + magma_data[idx + 1][
        1
      ] * dx);
      color[2] = 255 * (magma_data[idx][2] * (1. - dx) + magma_data[idx + 1][
        2
      ] * dx);
    } else {
      color[0] = 255 * magma_data[idx][0];
      color[1] = 255 * magma_data[idx][1];
      color[2] = 255 * magma_data[idx][2];
    }
    for (let ix = 0; ix < 20; ix++) {
      cbarData.data[4 * (iy * 20 + ix)] = color[0];
      cbarData.data[4 * (iy * 20 + ix) + 1] = color[1];
      cbarData.data[4 * (iy * 20 + ix) + 2] = color[2];
      cbarData.data[4 * (iy * 20 + ix) + 3] = color[3];
    }
  }
  // done computing data, now actually draw
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.putImageData(imageData, 0, 0);
  ctx.putImageData(cbarData, resolution + 20, 0);
  ctx.putImageData(logoData, resolution - 64, resolution / 2 - 64);
  /*ctx.putImageData(logoData, resolution - 200, resolution / 2 - 64);*/
  var mintick = Math.ceil(qmin);
  var maxtick = Math.floor(qmax);
  var Ntick = maxtick - mintick;
  var dtick = 1;
  while (Ntick > 6) {
    Ntick >>= 1;
    dtick <<= 1;
  }
  Ntick += 1;
  for (let i = 0; i < Ntick; i++) {
    var tick = mintick + i * dtick;
    var y = (tick - qmin) / (qmax - qmin);
    var tick_position = resolution / 2 * (1 - y);
    ctx.beginPath();
    ctx.moveTo(resolution + 40, tick_position);
    ctx.lineTo(resolution + 45, tick_position);
    ctx.stroke();
    ctx.font = "16px Times";
    ctx.fillText("10", resolution + 46, tick_position + 2);
    ctx.font = "12px Times";
    ctx.fillText(tick, resolution + 63, tick_position - 4);
///    ctx.font = "16px Times";
//    ctx.fillText(tick, resolution + 46, tick_position + 2);
  }
  ctx.save();
  ctx.translate(resolution + 110, resolution / 4);
  ctx.rotate(-0.5 * Math.PI);
  ctx.textAlign = "center";
  ctx.font = "20px Times";
  ctx.fillText(qfullname, 0, 0);
  ctx.restore();
}

var width = $("#lightcone_img").width();
$('#zslider').css('width', `${width-10}px`);
$('#qslider').css('width', `${width-10}px`);

/* only show the loader until we have all the image data loaded */
$('.lightconemap').hide();

var logoImage = new Image();
logoImage.addEventListener('load', load_logo, true);
logoImage.src = "assets/FLAMINGO_64x64.png";
/*logoImage.src = "assets/FLAMINGO_credit_black_64.png";*/
/* put the logo on the canvas to convert it to pixel values,
   then store it into an imageData array */
function load_logo() {
  ctx.drawImage(logoImage, 0, 0);
  logoData = ctx.getImageData(0, 0, 64, 64);
  /*logoData = ctx.getImageData(0, 0, 200, 64);*/
}

var imgmask = null;
var xhm = new XMLHttpRequest();
xhm.open('GET', "lightconedata/mask.dat", true);
xhm.responseType = "arraybuffer";
console.log("Waiting for image mask to load");
xhm.onload = function(e) {
  imgmask = new Uint32Array(this.response);
  console.log("Image mask loaded");
};
xhm.send();

var imgcube = null;
var xhr = new XMLHttpRequest();
/*xhr.open('GET', "assets/lightcone_all_maps.dat", true);*/
xhr.open('GET', "lightconedata/" + qname + "_lightcone_all_maps.dat", true);
xhr.responseType = "arraybuffer";
console.log("Waiting for lightcone cube to load");
xhr.onload = function(e) {
  var imgcube_int = new Uint8Array(this.response);
  imgcube = new Float64Array(imgcube_int.length);
  for (let imap = 0; imap < global_zimax; imap++) {
    var map_min = q_map_minmax[imap][0];
    var map_max = q_map_minmax[imap][1];
    for (let i = 0; i < resolution * resolution / 2; i++) {
      if (imgcube_int[imap * resolution * resolution / 2 + i] == 255) {
        imgcube[imap * resolution * resolution / 2 + i] = NaN;
      } else {
        imgcube[imap * resolution * resolution / 2 + i] = imgcube_int[imap *
            resolution * resolution / 2 + i] / 255. * (map_max - map_min) +
            map_min;
      }
    }
  }
  console.log("Lightcone cube loaded");
  update_qrange(); //to make sure initial values do not overlap
  update_img();
  $('.loader').hide();
  $('.lightconemap').show();
};
xhr.send();
