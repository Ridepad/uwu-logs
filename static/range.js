const THUMB_SIZE = 10;

function time_to_text(t) {
  const minutes = `${Math.floor(t/60)}`.padStart(2, '0');
  const seconds = `${t%60}`.padStart(2, '0');
  return `${minutes}:${seconds}`
}

function init(slider_div) {
  const query = new URLSearchParams(window.location.search);
  const rangemin = parseInt(query.get("s"));
  const rangemax = parseInt(query.get("f"));
  if (!rangemin || !rangemax) {
    slider_div.style.display = "none";
    return;
  }

  const minSlider = slider_div.querySelector('.min');
  const maxSlider = slider_div.querySelector('.max');
  const minValue = slider_div.querySelector('.min-value');
  const maxValue = slider_div.querySelector('.max-value');
  const totalValue = slider_div.querySelector('.total-value');

  const submit = slider_div.querySelector('.min-max-slider-submit');

  submit.addEventListener("click", () => {
    query.set("sc", minSlider.valueAsNumber);
    query.set("fc", maxSlider.valueAsNumber);
    window.location.replace(`?${query.toString()}`);
  })

  minSlider.setAttribute("min", rangemin);
  minSlider.setAttribute("max", rangemax-1);
  maxSlider.setAttribute("min", rangemin+1);
  maxSlider.setAttribute("max", rangemax);
  
  const customstart = parseInt(query.get("sc"));
  minSlider.value = customstart ? customstart : rangemin;
  const customend = parseInt(query.get("fc"));
  maxSlider.value = customend ? customend : rangemax;

  const _slider = document.querySelector(".min-max-slider");
  const rangewidth = _slider.offsetWidth / (rangemax - rangemin)

  function draw() {
    const min = minSlider.valueAsNumber;
    const max = maxSlider.valueAsNumber;

    const splitvalue = Math.floor((min + max) / 2);
    minSlider.setAttribute('max', splitvalue);
    maxSlider.setAttribute('min', splitvalue);

    // const width_p = Math.floor((splitvalue-min)/rangefull*100);
    // console.log(min, max, splitvalue, width_p)
    // const width_left = `${width_p}%`;
    // const width_right = `${100-width_p}%`;
    // minSlider.style.width = width_left;
    // maxSlider.style.width = width_right;
    // maxSlider.style.left = width_left;
    const width_left = THUMB_SIZE + (splitvalue - rangemin) * rangewidth;
    const width_right = THUMB_SIZE  + (rangemax - splitvalue) * rangewidth;
    minSlider.style.width = `${width_left}px`;
    maxSlider.style.width = `${width_right}px`;
    maxSlider.style.left = `${width_left}px`;

    
    minValue.innerText = time_to_text(min-rangemin);
    maxValue.innerText = time_to_text(max-rangemin);
    totalValue.innerText = `(${time_to_text(max-min)})`;

  }

  /* write legend */
  // const legend = document.createElement('div');
  // const legendnum = slider_div.getAttribute('data-legendnum');
  // legend.classList.add('legend');
  // for (var i = 0; i < legendnum; i++) {
  //   const div = document.createElement('div');
  //   div.innerText = Math.round(rangemin+(i/(legendnum-1))*(rangemax - rangemin));
  //   legend.appendChild(div);
  // } 
  // legend.style.marginTop = minSlider.offsetHeight+'px';
  // slider_div.appendChild(legend);

  draw();

  minSlider.addEventListener("input", draw);
  maxSlider.addEventListener("input", draw);
}

document.querySelectorAll('.min-max-slider').forEach(init);
