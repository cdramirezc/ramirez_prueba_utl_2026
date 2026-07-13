var DATA = {
  total_municipios: {
    TUNJA: 22993,
    SOGAMOSO: 358,
    PAIPA: 282,
  },
  top10: {
    PAIPA: [
      { nombre: "JOHN EDICKSON AMAYA RODRIGUEZ", codpar: "57", votos: 41 },
      { nombre: "ARIEL FERNANDO AVILA MARTINEZ", codpar: "57", votos: 11 },
      { nombre: "SOLEDAD TAMAYO TAMAYO", codpar: "3", votos: 6 },
      { nombre: "HORACIO JOSE SERPA MONCADA", codpar: "2", votos: 6 },
      { nombre: "RICHARD ALFONSO AGUILAR VILLA", codpar: "2", votos: 4 },
      { nombre: "CARLOS EDUARDO GUEVARA VILLABON", codpar: "43", votos: 4 },
      { nombre: "ENRIQUE GOMEZ MARTINEZ", codpar: "17", votos: 3 },
      { nombre: "LUIS EDUARDO DIAZ MATEUS", codpar: "3", votos: 3 },
      { nombre: "GLORIA ELSY DIAZ MARTINEZ", codpar: "43", votos: 3 },
      { nombre: "JUAN CARLOS BOCANEGRA CHACON", codpar: "57", votos: 3 },
    ],
    SOGAMOSO: [
      { nombre: "JUAN CAMILO OSTOS ROMERO", codpar: "17", votos: 27 },
      { nombre: "JOHN EDICKSON AMAYA RODRIGUEZ", codpar: "57", votos: 14 },
      { nombre: "GUSTAVO ADOLFO MORENO HURTADO", codpar: "57", votos: 11 },
      { nombre: "MIGUEL ANGEL BARRETO CASTILLO", codpar: "3", votos: 6 },
      { nombre: "ENRIQUE GOMEZ MARTINEZ", codpar: "17", votos: 5 },
      { nombre: "GERSSON VARGAS VALDELEON", codpar: "2", votos: 5 },
      { nombre: "HORACIO JOSE SERPA MONCADA", codpar: "2", votos: 5 },
      { nombre: "ARIEL FERNANDO AVILA MARTINEZ", codpar: "57", votos: 4 },
      { nombre: "JONATHAN FERNEY PULIDO HERNANDEZ", codpar: "57", votos: 3 },
      { nombre: "ANGELICA LISBETH LOZANO CORREA", codpar: "57", votos: 2 },
    ],
    TUNJA: [
      { nombre: "JOHN EDICKSON AMAYA RODRIGUEZ", codpar: "57", votos: 1971 },
      { nombre: "ARIEL FERNANDO AVILA MARTINEZ", codpar: "57", votos: 685 },
      { nombre: "JUAN CAMILO OSTOS ROMERO", codpar: "17", votos: 515 },
      { nombre: "JOHNNATAN ALEXIS TAMAYO USUGA", codpar: "3", votos: 272 },
      { nombre: "JONATHAN FERNEY PULIDO HERNANDEZ", codpar: "57", votos: 258 },
      { nombre: "CESAR AUGUSTO LOPEZ MORALES", codpar: "2", votos: 244 },
      { nombre: "GERSSON VARGAS VALDELEON", codpar: "2", votos: 233 },
      { nombre: "ANDREA PADILLA VILLARRAGA", codpar: "57", votos: 220 },
      { nombre: "CARLOS EDUARDO GUEVARA VILLABON", codpar: "43", votos: 217 },
      { nombre: "LUIS CARLOS RUA SANCHEZ", codpar: "57", votos: 213 },
    ],
  },
  lider_partido: {
    PAIPA: { codpar: "57", votos: 87 },
    SOGAMOSO: { codpar: "92", votos: 113 },
    TUNJA: { codpar: "92", votos: 6149 },
  },
  arrastre: {
    PAIPA: [
      {
        puesto: "I.E.EL ROSARIO SEDE CAMPESTRE",
        verde: 87,
        total: 282,
        ratio: 0.3085,
      },
    ],
    SOGAMOSO: [
      {
        puesto: "COL NZADO GUSTAVO JIMENEZ",
        verde: 51,
        total: 358,
        ratio: 0.1425,
      },
    ],
    TUNJA: [
      {
        puesto: "AUDITORIO GUSTAVO M CASTELLANOS COMFABOY",
        verde: 778,
        total: 3439,
        ratio: 0.2262,
      },
      {
        puesto: "C.A.S.D. BARRIO SAN ANTONIO",
        verde: 30,
        total: 246,
        ratio: 0.122,
      },
      {
        puesto: "COL DE BOYACA SD JOSE IGNACIO DE MARQUEZ",
        verde: 521,
        total: 2602,
        ratio: 0.2002,
      },
      {
        puesto: "COL. BOYACA FCO DE PAULA SANTANDER",
        verde: 915,
        total: 4304,
        ratio: 0.2126,
      },
      {
        puesto: "COLEGIO SALESIANO MALDONADO",
        verde: 1142,
        total: 5453,
        ratio: 0.2094,
      },
      {
        puesto: "I.T. GONZALO SUAREZ RENDON SEDE CENTRAL",
        verde: 619,
        total: 2570,
        ratio: 0.2409,
      },
      {
        puesto: "IES JUAN CASTELLANOS SD CRISANTO LUQUE",
        verde: 936,
        total: 4379,
        ratio: 0.2137,
      },
    ],
  },
};

var PARTY_COLORS = {
  57: "#007C34",
  92: "#7B2D8B",
  10: "#1E477D",
  2: "#E07B00",
};

function getPartyColor(codpar) {
  return PARTY_COLORS[codpar] || "#888";
}

function getPartyName(codpar) {
  var names = {
    57: "Alianza Verde",
    92: "Pacto Histórico",
    10: "Centro Democrático",
    2: "Conservador",
    3: "Cambio Radical",
    17: "Dignidad & Compromiso",
    43: "Partido 43",
    44: "Partido 44",
    55: "Partido 55",
    9: "Partido 9",
    40: "Partido 40",
    39: "Partido 39",
    34: "Partido 34",
    33: "Partido 33",
    18: "Partido 18",
    11: "Centro Democrático",
    6: "ASI",
    170: "Partido 170",
    188: "Partido 188",
    234: "Partido 234",
    237: "Partido 237",
    252: "Partido 252",
    285: "Partido 285",
    300: "Frente por la Vida",
    306: "Partido 306",
    347: "Partido 347",
  };
  return names[codpar] || "Partido " + codpar;
}

(function () {
  var muns = Object.keys(DATA.total_municipios).sort();
  var votos = muns.map(function (m) {
    return DATA.total_municipios[m];
  });
  var colors = muns.map(function (m) {
    var lider = DATA.lider_partido[m];
    return getPartyColor(lider ? lider.codpar : "");
  });

  var trace = {
    x: muns,
    y: votos,
    type: "bar",
    marker: { color: colors },
    text: votos.map(function (v) {
      return v.toLocaleString();
    }),
    textposition: "outside",
    textfont: { size: 14, color: "#333" },
    hovertemplate: "<b>%{x}</b><br>Votos: %{y:,.0f}<extra></extra>",
  };

  var layout = {
    title: {
      text: "Total Votos Senado 2026 por Municipio",
      font: { size: 18 },
    },
    xaxis: { title: "Municipio", tickfont: { size: 14 } },
    yaxis: { title: "Votos", gridcolor: "#e0e0e0" },
    plot_bgcolor: "#fafafa",
    paper_bgcolor: "#fff",
    margin: { t: 50, r: 30, b: 50, l: 60 },
    hoverlabel: { bgcolor: "#0f3460", font: { color: "#fff" } },
  };

  Plotly.newPlot("chartComparativo", [trace], layout, { responsive: true });
})();

var municipalities = Object.keys(DATA.total_municipios).sort();
var selCandidatos = document.getElementById("selMunicipioCandidatos");
var selArrastre = document.getElementById("selMunicipioArrastre");
var chartCandidatos = null;
var chartArrastre = null;

municipalities.forEach(function (m) {
  var opt1 = document.createElement("option");
  opt1.value = m;
  opt1.textContent = m;
  selCandidatos.appendChild(opt1);
  var opt2 = document.createElement("option");
  opt2.value = m;
  opt2.textContent = m;
  selArrastre.appendChild(opt2);
});

function renderCandidatos(mun) {
  var cands = DATA.top10[mun] || [];
  var lider = DATA.lider_partido[mun];

  var info = document.getElementById("infoLider");
  if (lider) {
    info.innerHTML =
      "<strong>Partido líder SE:</strong> " +
      getPartyName(lider.codpar) +
      " (codpar " +
      lider.codpar +
      ") — <strong>" +
      lider.votos.toLocaleString() +
      "</strong> votos";
  }

  var tbody = document.querySelector("#tablaCandidatos tbody");
  tbody.innerHTML = "";
  cands.forEach(function (c, i) {
    var tr = document.createElement("tr");
    tr.innerHTML =
      "<td>" +
      (i + 1) +
      "</td><td>" +
      c.nombre +
      '</td><td><span class="badge" style="background:' +
      getPartyColor(c.codpar) +
      '">' +
      getPartyName(c.codpar) +
      "</span></td><td>" +
      c.votos.toLocaleString() +
      "</td>";
    tbody.appendChild(tr);
  });

  var ctx = document.getElementById("chartCandidatos").getContext("2d");
  if (chartCandidatos) chartCandidatos.destroy();

  var labels = cands.map(function (c) {
    return c.nombre.substring(0, 20) + (c.nombre.length > 20 ? "..." : "");
  });
  var values = cands.map(function (c) {
    return c.votos;
  });
  var barColors = cands.map(function (c) {
    return getPartyColor(c.codpar);
  });

  chartCandidatos = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Votos",
          data: values,
          backgroundColor: barColors,
          borderColor: barColors.map(function (c) {
            return c;
          }),
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return ctx.raw.toLocaleString() + " votos";
            },
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Votos", font: { weight: "bold" } },
          grid: { color: "#e8e8e8" },
        },
        y: {
          ticks: { font: { size: 10 } },
          grid: { display: false },
        },
      },
    },
  });
}

selCandidatos.addEventListener("change", function () {
  renderCandidatos(this.value);
});
renderCandidatos(municipalities[0]);

function renderArrastre(mun) {
  var data = DATA.arrastre[mun] || [];
  var ctx = document.getElementById("chartArrastre").getContext("2d");
  if (chartArrastre) chartArrastre.destroy();

  var labels = data.map(function (d) {
    return d.puesto;
  });
  var ratios = data.map(function (d) {
    return d.ratio;
  });
  var verdes = data.map(function (d) {
    return d.verde;
  });
  var totals = data.map(function (d) {
    return d.total;
  });

  chartArrastre = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Ratio Verde / Total",
          data: ratios,
          backgroundColor: "rgba(0,124,52,0.7)",
          borderColor: "#007C34",
          borderWidth: 2,
          borderRadius: 4,
          order: 2,
          yAxisID: "y",
        },
        {
          label: "Votos Verde",
          data: verdes,
          backgroundColor: "rgba(0,124,52,0.15)",
          borderColor: "#007C34",
          borderWidth: 1,
          borderDash: [4, 4],
          type: "line",
          pointRadius: 4,
          pointBackgroundColor: "#007C34",
          fill: false,
          order: 1,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              var i = ctx.dataIndex;
              if (ctx.datasetIndex === 0) return "Ratio: " + ctx.raw.toFixed(4);
              return (
                "Votos: " +
                ctx.raw.toLocaleString() +
                " / Total: " +
                totals[i].toLocaleString()
              );
            },
          },
        },
      },
      scales: {
        y: {
          position: "left",
          title: { display: true, text: "Ratio Verde / Total" },
          min: 0,
          max: Math.max(1.0, Math.max.apply(null, ratios) * 1.3),
          grid: { color: "#e8e8e8" },
        },
        y1: {
          position: "right",
          title: { display: true, text: "Votos Verde" },
          grid: { display: false },
          beginAtZero: true,
        },
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            font: { size: 9 },
          },
          grid: { display: false },
        },
      },
    },
    plugins: [
      {
        id: "referenceLine",
        afterDraw: function (chart) {
          var yScale = chart.scales.y;
          var ctx = chart.ctx;
          var yPixel = yScale.getPixelForValue(1.0);
          if (
            yPixel === undefined ||
            yPixel < yScale.top ||
            yPixel > yScale.bottom
          )
            return;

          ctx.save();
          ctx.beginPath();
          ctx.strokeStyle = "#E07B00";
          ctx.lineWidth = 2;
          ctx.setLineDash([8, 6]);
          ctx.moveTo(yScale.left, yPixel);
          ctx.lineTo(yScale.right, yPixel);
          ctx.stroke();

          ctx.fillStyle = "#E07B00";
          ctx.font = "bold 12px sans-serif";
          ctx.textAlign = "right";
          ctx.fillText("Referencia 1.0", yScale.right - 4, yPixel - 6);
          ctx.restore();
        },
      },
    ],
  });
}

selArrastre.addEventListener("change", function () {
  renderArrastre(this.value);
});
renderArrastre(municipalities[0]);
