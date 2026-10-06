(function () {
    var KEY = "letterSite.v2";
    var MAX_PHOTOS = 4;
    var EMOJIS = [
        "\uD83D\uDC8C", "\uD83C\uDF37", "\uD83C\uDF19", "\u2728",
        "\uD83E\uDD0D", "\uD83E\uDEF6", "\uD83C\uDF38", "\uD83E\uDD8B",
        "\uD83D\uDD4A\uFE0F", "\uD83C\uDF42", "\uD83C\uDF39", "\u2601\uFE0F",
        "\uD83E\uDD79", "\uD83D\uDCAB", "\uD83E\uDDF8", "\uD83C\uDF3B"
    ];

    function el(id) { return document.getElementById(id); }

    var state = { to: "", body: "", from: "", date: "", theme: "rose", photos: [] };
    try {
        var saved = JSON.parse(localStorage.getItem(KEY));
        if (saved) {
            for (var k in saved) { state[k] = saved[k]; }
        }
    } catch (e) { }
    if (!state.date) { state.date = new Date().toISOString().slice(0, 10); }

    function save() {
        try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { }
    }

    function setText(node, text, dim) {
        node.textContent = text;
        if (dim) { node.classList.add("dim"); } else { node.classList.remove("dim"); }
    }

    function renderLetter() {
        var d = new Date(state.date + "T00:00:00");
        el("lDate").textContent = isNaN(d.getTime()) ? "" :
            d.toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });

        setText(el("lTo"), state.to ? "Dear " + state.to + "," : "Dear you,", !state.to);
        setText(el("lBody"), state.body ? state.body : "Your words will appear here as you write...", !state.body);
        setText(el("lFrom"), state.from ? "With love, " + state.from + " \uD83E\uDD0D" : "", false);

        var box = el("lPhotos");
        box.innerHTML = "";
        state.photos.forEach(function (p) {
            var fig = document.createElement("div");
            fig.className = "polaroid";
            var img = document.createElement("img");
            img.src = p.src;
            img.alt = p.caption || "Photo in the letter";
            var cap = document.createElement("span");
            cap.textContent = p.caption || "";
            fig.appendChild(img);
            fig.appendChild(cap);
            box.appendChild(fig);
        });
    }

    function renderPhotoList() {
        var list = el("photoList");
        list.innerHTML = "";
        state.photos.forEach(function (p, i) {
            var row = document.createElement("div");
            row.className = "photo-item";

            var img = document.createElement("img");
            img.src = p.src;
            img.alt = "";

            var cap = document.createElement("input");
            cap.type = "text";
            cap.placeholder = "Caption (optional)";
            cap.maxLength = 40;
            cap.value = p.caption || "";
            cap.addEventListener("input", function () {
                state.photos[i].caption = cap.value;
                renderLetter();
                save();
            });

            var del = document.createElement("button");
            del.type = "button";
            del.textContent = "\u00D7";
            del.setAttribute("aria-label", "Remove photo");
            del.addEventListener("click", function () {
                state.photos.splice(i, 1);
                renderPhotoList();
                renderLetter();
                save();
            });

            row.appendChild(img);
            row.appendChild(cap);
            row.appendChild(del);
            list.appendChild(row);
        });
        el("addPhoto").style.display = state.photos.length >= MAX_PHOTOS ? "none" : "block";
    }

    // Shrinks big photos so they fit in browser storage
    function shrink(file, done) {
        var reader = new FileReader();
        reader.onload = function () {
            var img = new Image();
            img.onload = function () {
                var scale = Math.min(1, 700 / Math.max(img.width, img.height));
                var c = document.createElement("canvas");
                c.width = Math.round(img.width * scale);
                c.height = Math.round(img.height * scale);
                c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
                done(c.toDataURL("image/jpeg", 0.8));
            };
            img.src = reader.result;
        };
        reader.readAsDataURL(file);
    }

    el("addPhoto").addEventListener("click", function () { el("file").click(); });
    el("file").addEventListener("change", function (e) {
        var files = Array.prototype.slice.call(e.target.files);
        files.forEach(function (f) {
            if (state.photos.length >= MAX_PHOTOS) { return; }
            shrink(f, function (dataUrl) {
                if (state.photos.length >= MAX_PHOTOS) { return; }
                state.photos.push({ src: dataUrl, caption: "" });
                renderPhotoList();
                renderLetter();
                save();
            });
        });
        e.target.value = "";
    });

    // Text fields
    ["to", "body", "from", "date"].forEach(function (key) {
        el(key).value = state[key];
        el(key).addEventListener("input", function () {
            state[key] = el(key).value;
            renderLetter();
            save();
        });
    });

    // Emoji buttons (insert where the cursor is)
    EMOJIS.forEach(function (em) {
        var b = document.createElement("button");
        b.type = "button";
        b.textContent = em;
        b.addEventListener("click", function () {
            var t = el("body");
            var s = t.selectionStart;
            var e = t.selectionEnd;
            t.value = t.value.slice(0, s) + em + t.value.slice(e);
            t.selectionStart = t.selectionEnd = s + em.length;
            t.focus();
            state.body = t.value;
            renderLetter();
            save();
        });
        el("emojis").appendChild(b);
    });

    // Moods
    function setTheme(t) {
        state.theme = t;
        document.body.className = t === "rose" ? "" : t;
        var btns = el("themes").getElementsByTagName("button");
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].getAttribute("data-t") === t) { btns[i].classList.add("on"); }
            else { btns[i].classList.remove("on"); }
        }
        save();
    }
    var themeBtns = el("themes").getElementsByTagName("button");
    for (var i = 0; i < themeBtns.length; i++) {
        (function (b) {
            b.addEventListener("click", function () { setTheme(b.getAttribute("data-t")); });
        })(themeBtns[i]);
    }

    // Envelope
    var overlay = el("overlay");
    el("sealBtn").addEventListener("click", function () {
        var stage = el("stage");
        stage.innerHTML = "";
        stage.className = "";
        var copy = el("letter").cloneNode(true);
        copy.removeAttribute("id");
        stage.appendChild(copy);
        el("env").className = "env";
        el("envBox").style.display = "block";
        el("backBtn").style.display = "none";
        overlay.className = "show";
        overlay.scrollTop = 0;
    });
    el("env").addEventListener("click", function () {
        el("env").className = "env open";
        setTimeout(function () {
            el("envBox").style.display = "none";
            el("stage").className = "show";
            el("backBtn").style.display = "block";
        }, 800);
    });
    el("backBtn").addEventListener("click", function () { overlay.className = ""; });

    el("printBtn").addEventListener("click", function () { window.print(); });

    // Start
    setTheme(state.theme);
    renderPhotoList();
    renderLetter();
}
)
    ();