import PDFObject from "https://esm.run/pdfobject@2.2.12";

const pdfElem = document.getElementById("pdf-preview");
const resumeForm = document.getElementById("resume");
const generateButton = document.getElementById("generate-button");

const persistedInputs = [`input:not([type="file"])`, `textarea`].join(", ");

// Automatically persist form data to localStorage.
for (const input of resumeForm.querySelectorAll(persistedInputs)) {
  input.addEventListener("change", () => {
    localStorage.setItem(input.name, input.value);
  });
  const value = localStorage.getItem(input.name);
  if (value !== null) {
    input.value = value;
  }
}

async function generateNow() {
  if (!PDFObject || !PDFObject.supportsPDFs) {
    throw "Unfortunately, your browser does not support embedded PDFs :(";
  }

  const formData = new FormData(resumeForm);

  function applyLimit(object, name) {
    const limit = parseInt(formData.get(`${name}-limit`));
    console.log(`Limit for ${name} is ${limit}`);
    if (limit > -1) {
      object[name] = object[name].slice(0, limit);
    }
  }

  const resumeFile = formData.get("file");
  if (!resumeFile || !(resumeFile instanceof File)) {
    throw "Please upload a resume.";
  }
  const resumeData = await resumeFile.arrayBuffer();
  let resumeJSON = new TextDecoder("utf-8").decode(resumeData);

  const resume = JSON.parse(resumeJSON);
  applyLimit(resume, "work");
  applyLimit(resume, "education");
  applyLimit(resume, "projects");
  applyLimit(resume, "awards");
  resumeJSON = JSON.stringify(resume);

  const params = new URLSearchParams();
  for (const param of [
    "query",
    "work",
    "education",
    "skills",
    "projects",
    "awards",
  ]) {
    params.set(param, formData.get(param));
  }

  console.log("/api/resume/sort?" + params.toString());

  // Replace the resumeJSON with the one from the server.
  resumeJSON = await mustFetch("/api/resume/sort?" + params.toString(), {
    method: "POST",
    body: resumeJSON,
    headers: { "Content-Type": "application/json" },
  })
    .then((r) => r.json())
    .then((j) => j.resume)
    .then((r) => JSON.stringify(r));

  const resumePDF = await mustFetch("/api/resume.pdf", {
    method: "POST",
    body: resumeJSON,
    headers: { "Content-Type": "application/json" },
  })
    .then((r) => r.blob())
    .then((b) => blobToDataURL(b));

  console.log(resumePDF);
  pdfElem.innerHTML = "";
  PDFObject.embed(resumePDF, pdfElem);
}

async function blobToDataURL(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (event) => resolve(event.target.result);
    reader.readAsDataURL(blob);
  });
}

// mustFetch wraps fetch() to throw an error if the response is not OK.
async function mustFetch(path, opts = {}) {
  const resp = await fetch(path, opts);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`fetch error: ${resp.statusText} ${text}`);
  }
  return resp;
}

let generating = false;
let keepGenerating = false;

// generate guards generateNow from being called multiple times at the same
// time. It ensures that the PDF is only generated once at a time. If
// generateNow is called multiple times while it is still generating, it will
// defer the next generation until the current one is finished.
function generate() {
  if (generating) {
    keepGenerating = true;
    return;
  }

  generating = true;
  generateButton.disabled = true;

  generateNow()
    .catch((err) => {
      console.error("Error generating PDF:", err);

      const span = document.createElement("span");
      span.classList.add("error");
      span.innerHTML = `<b>Error:</b><br />`;
      span.append(`${err}`);
      pdfElem.innerHTML = "";
      pdfElem.appendChild(span);
    })
    .finally(() => {
      generating = false;
      generateButton.disabled = false;
      if (keepGenerating) {
        keepGenerating = false;
        generate();
      }
    });
}

window.handleGenerate = function (ev) {
  ev.preventDefault();
  generate();
};
