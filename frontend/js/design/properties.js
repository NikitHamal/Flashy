const DesignProperties = {
    activeElement: null,

    init() {
        this.bindInputs();
        return this;
    },

    bindInputs() {
        const binding = [
            { id: "prop-fill", attr: "fill" },
            { id: "prop-stroke", attr: "stroke" },
            { id: "prop-stroke-width", attr: "stroke-width" },
            { id: "prop-opacity", attr: "opacity", scale: 0.01 },
            { id: "prop-font-size", attr: "font-size" },
            { id: "prop-font-family", attr: "font-family" },
            { id: "prop-font-weight", attr: "font-weight" }
        ];

        binding.forEach((item) => {
            const input = document.getElementById(item.id);
            if (!input) return;
            input.addEventListener("input", () => {
                if (!this.activeElement) return;
                const value = item.scale ? (parseFloat(input.value) * item.scale).toString() : input.value;
                DesignCanvas.updateSelectedAttributes({ [item.attr]: value });
                if (item.id === "prop-fill") {
                    document.getElementById("prop-fill-hex").value = input.value;
                }
                if (item.id === "prop-stroke") {
                    document.getElementById("prop-stroke-hex").value = input.value;
                }
                if (item.id === "prop-opacity") {
                    const label = document.getElementById("prop-opacity-value");
                    if (label) label.textContent = `${input.value}%`;
                }
            });
        });

        document.getElementById("prop-fill-hex")?.addEventListener("input", (e) => {
            document.getElementById("prop-fill").value = e.target.value;
            DesignCanvas.updateSelectedAttributes({ fill: e.target.value });
        });

        document.getElementById("prop-stroke-hex")?.addEventListener("input", (e) => {
            document.getElementById("prop-stroke").value = e.target.value;
            DesignCanvas.updateSelectedAttributes({ stroke: e.target.value });
        });

        document.getElementById("prop-x")?.addEventListener("input", (e) => this.updatePosition("x", e.target.value));
        document.getElementById("prop-y")?.addEventListener("input", (e) => this.updatePosition("y", e.target.value));
        document.getElementById("prop-width")?.addEventListener("input", (e) => this.updateSize("width", e.target.value));
        document.getElementById("prop-height")?.addEventListener("input", (e) => this.updateSize("height", e.target.value));
        document.getElementById("prop-radius")?.addEventListener("input", (e) => {
            if (!this.activeElement || this.activeElement.tagName !== "rect") return;
            const val = parseFloat(e.target.value);
            if (Number.isNaN(val)) return;
            DesignCanvas.updateSelectedAttributes({ rx: val, ry: val });
            const label = document.getElementById("prop-radius-value");
            if (label) label.textContent = val;
        });

        document.getElementById("prop-text")?.addEventListener("input", (e) => {
            if (!this.activeElement || this.activeElement.tagName !== "text") return;
            this.activeElement.textContent = e.target.value;
        });
    },

    updatePosition(axis, value) {
        if (!this.activeElement) return;
        const tag = this.activeElement.tagName;
        const val = parseFloat(value);
        if (Number.isNaN(val)) return;
        if (tag === "rect" || tag === "image") {
            DesignCanvas.updateSelectedAttributes({ [axis]: val });
        } else if (tag === "circle") {
            const attr = axis === "x" ? "cx" : "cy";
            DesignCanvas.updateSelectedAttributes({ [attr]: val });
        } else if (tag === "text") {
            const attr = axis === "x" ? "x" : "y";
            DesignCanvas.updateSelectedAttributes({ [attr]: val });
        } else if (tag === "line") {
            const attr = axis === "x" ? "x1" : "y1";
            DesignCanvas.updateSelectedAttributes({ [attr]: val });
        }
    },

    updateSize(dimension, value) {
        if (!this.activeElement) return;
        const tag = this.activeElement.tagName;
        const val = parseFloat(value);
        if (Number.isNaN(val)) return;
        if (tag === "rect" || tag === "image") {
            DesignCanvas.updateSelectedAttributes({ [dimension]: val });
        } else if (tag === "circle") {
            DesignCanvas.updateSelectedAttributes({ r: val / 2 });
        }
    },

    updateFromSelection(element) {
        this.activeElement = element;
        const noSelection = document.getElementById("no-selection");
        const props = document.getElementById("object-properties");
        if (!element) {
            noSelection?.classList.remove("hidden");
            props?.classList.add("hidden");
            return;
        }
        noSelection?.classList.add("hidden");
        props?.classList.remove("hidden");

        const tag = element.tagName;
        const getAttr = (name, fallback = "") => element.getAttribute(name) || fallback;
        document.getElementById("prop-fill").value = getAttr("fill", "#ffb000");
        document.getElementById("prop-fill-hex").value = getAttr("fill", "#ffb000");
        document.getElementById("prop-stroke").value = getAttr("stroke", "#14120e");
        document.getElementById("prop-stroke-hex").value = getAttr("stroke", "#14120e");
        document.getElementById("prop-stroke-width").value = getAttr("stroke-width", "3");
        document.getElementById("prop-opacity").value = Math.round(parseFloat(getAttr("opacity", "1")) * 100);
        const opacityLabel = document.getElementById("prop-opacity-value");
        if (opacityLabel) opacityLabel.textContent = `${document.getElementById("prop-opacity").value}%`;

        if (tag === "rect" || tag === "image") {
            document.getElementById("prop-x").value = getAttr("x", 0);
            document.getElementById("prop-y").value = getAttr("y", 0);
            document.getElementById("prop-width").value = getAttr("width", 100);
            document.getElementById("prop-height").value = getAttr("height", 100);
            const radiusRow = document.getElementById("corner-radius-row");
            if (radiusRow) radiusRow.style.display = tag === "rect" ? "block" : "none";
            if (tag === "rect") {
                const rx = getAttr("rx", 0);
                document.getElementById("prop-radius").value = rx;
                const label = document.getElementById("prop-radius-value");
                if (label) label.textContent = rx;
            }
        } else if (tag === "circle") {
            document.getElementById("prop-x").value = getAttr("cx", 0);
            document.getElementById("prop-y").value = getAttr("cy", 0);
            const r = parseFloat(getAttr("r", 50));
            document.getElementById("prop-width").value = r * 2;
            document.getElementById("prop-height").value = r * 2;
            const radiusRow = document.getElementById("corner-radius-row");
            if (radiusRow) radiusRow.style.display = "none";
        } else if (tag === "text") {
            document.getElementById("prop-x").value = getAttr("x", 0);
            document.getElementById("prop-y").value = getAttr("y", 0);
            document.getElementById("prop-width").value = "";
            document.getElementById("prop-height").value = "";
            const radiusRow = document.getElementById("corner-radius-row");
            if (radiusRow) radiusRow.style.display = "none";
        }

        const textProps = document.getElementById("text-properties");
        if (tag === "text") {
            textProps.style.display = "block";
            document.getElementById("prop-font-family").value = getAttr("font-family", "Space Grotesk");
            document.getElementById("prop-font-size").value = getAttr("font-size", "24");
            document.getElementById("prop-font-weight").value = getAttr("font-weight", "700");
            document.getElementById("prop-text").value = element.textContent || "";
        } else {
            textProps.style.display = "none";
        }
    }
};
