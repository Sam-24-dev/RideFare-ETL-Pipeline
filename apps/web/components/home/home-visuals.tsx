export function HomeBackdrop(): React.ReactElement {
  return (
    <div className="pointer-events-none absolute inset-0 opacity-[0.34]">
      <svg className="h-full w-full" preserveAspectRatio="none" viewBox="0 0 1440 2200">
        <g fill="none" stroke="rgba(178,115,64,0.18)" strokeWidth="1.1">
          <path d="M-60 100 C180 20 320 210 540 120 S980 40 1180 160 S1500 180 1600 110" />
          <path d="M-80 180 C120 120 320 290 520 220 S930 140 1180 250 S1500 290 1620 190" />
          <path d="M-80 260 C140 210 330 360 560 300 S980 220 1210 340 S1490 380 1600 300" />
          <path d="M-100 340 C160 300 330 440 560 390 S980 320 1220 430 S1490 470 1620 390" />
          <path d="M-120 420 C120 390 360 520 570 470 S1000 420 1220 520 S1480 560 1620 470" />
          <path d="M-120 500 C140 470 370 600 590 560 S1020 500 1240 610 S1490 660 1620 580" />
          <path d="M-140 1320 C160 1270 300 1450 550 1390 S980 1310 1210 1430 S1510 1460 1620 1360" />
          <path d="M-140 1400 C170 1360 300 1510 560 1460 S980 1390 1230 1510 S1510 1540 1640 1450" />
          <path d="M-120 1480 C170 1450 310 1580 580 1540 S1000 1470 1240 1590 S1510 1610 1640 1530" />
          <path d="M-110 1560 C170 1530 320 1660 580 1615 S1000 1540 1240 1670 S1510 1710 1640 1615" />
          <path d="M-80 1640 C170 1600 330 1740 580 1690 S1000 1620 1240 1740 S1500 1790 1640 1695" />
          <path d="M-70 1720 C200 1690 340 1810 600 1760 S1010 1700 1260 1810 S1500 1850 1640 1775" />
        </g>
      </svg>
    </div>
  );
}

export function HeroTerrainGraphic(): React.ReactElement {
  return (
    <svg className="h-full w-full" preserveAspectRatio="xMidYMid slice" viewBox="0 0 1600 860">
      <defs>
        <linearGradient id="terrain-wash" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#fffdf9" />
          <stop offset="48%" stopColor="#f8f2ea" />
          <stop offset="100%" stopColor="#ebe0d2" />
        </linearGradient>
        <radialGradient id="copper-glow" cx="76%" cy="38%" r="42%">
          <stop offset="0%" stopColor="rgba(178,115,64,0.28)" />
          <stop offset="100%" stopColor="rgba(178,115,64,0)" />
        </radialGradient>
        <radialGradient id="lagoon-glow" cx="64%" cy="66%" r="34%">
          <stop offset="0%" stopColor="rgba(31,90,126,0.18)" />
          <stop offset="100%" stopColor="rgba(31,90,126,0)" />
        </radialGradient>
        <radialGradient id="contour-mass" cx="82%" cy="72%" r="30%">
          <stop offset="0%" stopColor="rgba(203,167,128,0.30)" />
          <stop offset="100%" stopColor="rgba(203,167,128,0)" />
        </radialGradient>
        <linearGradient id="contour-fade" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stopColor="white" stopOpacity="0" />
          <stop offset="28%" stopColor="white" stopOpacity="0.12" />
          <stop offset="44%" stopColor="white" stopOpacity="0.76" />
          <stop offset="100%" stopColor="white" stopOpacity="1" />
        </linearGradient>
        <mask id="hero-contours">
          <rect width="1600" height="860" fill="url(#contour-fade)" />
        </mask>
        <filter id="soft-blur" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="22" />
        </filter>
      </defs>

      <rect width="1600" height="860" fill="url(#terrain-wash)" />
      <rect width="1600" height="860" fill="url(#copper-glow)" />
      <rect width="1600" height="860" fill="url(#lagoon-glow)" />
      <rect width="1600" height="860" fill="url(#contour-mass)" />

      <g opacity="0.55" filter="url(#soft-blur)">
        <path
          d="M790 686 C956 592 1064 488 1200 430 C1308 384 1438 336 1576 246"
          fill="none"
          stroke="rgba(31,90,126,0.22)"
          strokeWidth="30"
          strokeLinecap="round"
        />
        <path
          d="M730 744 C922 664 1080 580 1218 514 C1360 446 1458 382 1560 312"
          fill="none"
          stroke="rgba(178,115,64,0.18)"
          strokeWidth="38"
          strokeLinecap="round"
        />
      </g>

      <g mask="url(#hero-contours)" fill="none" strokeLinecap="round">
        <g stroke="rgba(176,118,72,0.34)" strokeWidth="1.4">
          <path d="M520 626 C674 552 790 530 900 504 C1008 478 1108 410 1198 380 C1308 342 1424 364 1598 254" />
          <path d="M496 656 C650 586 770 566 884 544 C996 522 1092 450 1186 422 C1290 390 1408 404 1598 294" />
          <path d="M340 694 C522 630 646 678 784 650 C920 622 1008 528 1138 510 C1286 490 1392 526 1618 424" />
          <path d="M342 662 C516 604 658 648 788 620 C918 592 1018 510 1148 492 C1286 472 1404 506 1618 406" />
          <path d="M346 628 C530 576 662 614 800 590 C928 568 1018 486 1152 470 C1300 452 1418 490 1620 382" />
          <path d="M358 594 C542 548 676 586 812 560 C942 538 1036 458 1168 444 C1316 426 1422 462 1620 356" />
          <path d="M372 560 C552 518 684 552 824 530 C950 512 1050 432 1180 418 C1320 402 1440 438 1620 336" />
          <path d="M388 526 C566 488 700 520 840 502 C966 484 1058 410 1188 398 C1328 386 1448 418 1620 316" />
          <path d="M404 494 C580 460 714 492 854 474 C978 458 1072 390 1200 382 C1338 372 1460 398 1620 298" />
          <path d="M420 462 C596 432 728 466 868 448 C992 432 1086 374 1212 366 C1348 358 1466 384 1620 284" />
          <path d="M438 430 C612 404 742 440 882 424 C1004 410 1098 358 1226 352 C1360 346 1480 370 1620 272" />
          <path d="M456 398 C626 376 758 416 900 402 C1020 390 1114 344 1242 340 C1374 336 1488 356 1620 260" />
          <path d="M476 366 C644 348 772 392 916 382 C1036 374 1128 332 1256 328 C1390 324 1500 344 1622 248" />
          <path d="M496 336 C662 322 790 374 936 366 C1050 358 1140 322 1268 320 C1404 318 1510 334 1622 240" />
          <path d="M694 310 C834 274 928 258 1040 246 C1148 236 1212 184 1300 154 C1386 124 1490 138 1608 102" />
          <path d="M730 284 C866 252 958 236 1068 228 C1174 220 1238 176 1324 148 C1408 120 1502 132 1608 98" />
        </g>

        <g stroke="rgba(31,90,126,0.18)" strokeWidth="1.15">
          <path d="M714 730 C900 648 1034 568 1188 492 C1320 426 1454 356 1608 244" />
          <path d="M744 742 C936 660 1072 586 1224 518 C1352 460 1474 396 1608 292" />
          <path d="M778 758 C970 684 1110 612 1262 548 C1380 500 1490 446 1608 346" />
        </g>

        <path
          d="M612 706 C772 650 894 564 1020 500 C1152 432 1270 388 1412 276 C1482 220 1538 166 1608 104"
          stroke="rgba(31,90,126,0.66)"
          strokeWidth="5.4"
        />
        <path
          d="M558 742 C728 712 858 654 1000 594 C1152 528 1280 462 1394 396 C1484 344 1548 292 1604 246"
          stroke="rgba(176,118,72,0.82)"
          strokeWidth="3.9"
        />
      </g>

      <g opacity="0.24" stroke="rgba(31,90,126,0.18)" strokeWidth="1">
        <path d="M880 90 V748" />
        <path d="M1000 90 V748" />
        <path d="M1120 90 V748" />
        <path d="M1240 90 V748" />
        <path d="M1360 90 V748" />
        <path d="M1480 90 V748" />
      </g>
    </svg>
  );
}

export function TerminalPreviewGraphic(): React.ReactElement {
  return (
    <svg className="h-full w-full" viewBox="0 0 620 360">
      <rect width="620" height="360" fill="#131e26" />
      <g opacity="0.16" stroke="#e7ddd0" strokeWidth="1">
        <path d="M0 90 H620" />
        <path d="M0 180 H620" />
        <path d="M0 270 H620" />
        <path d="M120 0 V360" />
        <path d="M240 0 V360" />
        <path d="M360 0 V360" />
        <path d="M480 0 V360" />
      </g>
      <g fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d="M45 270 C120 205 165 170 250 165 S395 170 565 92" stroke="#b27340" strokeWidth="3.4" />
        <path d="M72 305 C155 238 205 205 290 202 S430 205 585 125" stroke="#1f5a7e" strokeWidth="2.8" />
        <path d="M150 60 C190 110 215 130 250 165" stroke="#b27340" strokeWidth="2.3" />
        <path d="M455 50 C442 82 432 110 410 138" stroke="#1f5a7e" strokeWidth="2.1" />
      </g>
      <g>
        <circle cx="250" cy="165" r="14" fill="#f4efe7" />
        <circle cx="290" cy="202" r="9" fill="#b27340" />
        <circle cx="565" cy="92" r="9" fill="#f4efe7" />
        <circle cx="585" cy="125" r="7" fill="#b27340" />
        <circle cx="45" cy="270" r="7" fill="#f4efe7" />
      </g>
      <rect x="390" y="26" width="188" height="64" fill="rgba(244,239,231,0.08)" stroke="rgba(244,239,231,0.2)" />
      <rect x="402" y="40" width="74" height="10" fill="#b27340" opacity="0.72" />
      <rect x="402" y="59" width="146" height="9" fill="#f4efe7" opacity="0.6" />
      <rect x="32" y="32" width="138" height="42" fill="rgba(244,239,231,0.08)" stroke="rgba(244,239,231,0.16)" />
      <text x="48" y="58" fill="#f4efe7" fontFamily="IBM Plex Mono, monospace" fontSize="14" letterSpacing="2">
        LIVE GRID
      </text>
    </svg>
  );
}

export function MethodologyPreviewGraphic(): React.ReactElement {
  return (
    <svg className="h-full w-full" viewBox="0 0 620 360">
      <rect width="620" height="360" fill="#fbf7f1" />
      <g stroke="#b27340" strokeWidth="1.3" fill="none" opacity="0.52">
        <path d="M70 270 H550" />
        <path d="M130 90 V270" />
        <path d="M250 90 V270" />
        <path d="M370 90 V270" />
        <path d="M490 90 V270" />
        <path d="M130 90 H490" />
        <path d="M130 150 H490" />
        <path d="M130 210 H490" />
      </g>
      <g stroke="#1f5a7e" strokeWidth="2.2" opacity="0.45">
        <path d="M120 300 C180 250 210 190 280 155 S400 115 520 80" />
        <path d="M80 260 C165 240 215 212 270 160" />
      </g>
      <g fill="#15242d" fontFamily="IBM Plex Mono, monospace" fontSize="11" letterSpacing="1.6">
        <text x="74" y="54">VIAJES + CLIMA</text>
        <text x="248" y="54">VALIDACION</text>
        <text x="402" y="54">MARTS</text>
      </g>
    </svg>
  );
}

export function LabPreviewGraphic(): React.ReactElement {
  return (
    <svg className="h-full w-full" viewBox="0 0 980 360">
      <rect width="980" height="360" fill="#171311" />
      <g opacity="0.12" stroke="#f4efe7" strokeWidth="1">
        <path d="M0 90 H980" />
        <path d="M0 180 H980" />
        <path d="M0 270 H980" />
        <path d="M160 0 V360" />
        <path d="M320 0 V360" />
        <path d="M480 0 V360" />
        <path d="M640 0 V360" />
        <path d="M800 0 V360" />
      </g>
      <g fill="none" strokeLinecap="round">
        <path d="M60 250 L300 170 L470 195 L690 110 L900 60" stroke="#b27340" strokeWidth="4" />
        <path d="M60 280 L300 240 L470 208 L690 168 L900 112" stroke="#1f5a7e" strokeWidth="3" />
      </g>
      <g fill="#b27340" opacity="0.9">
        <rect x="72" y="208" width="24" height="74" />
        <rect x="116" y="188" width="24" height="94" />
        <rect x="160" y="170" width="24" height="112" />
        <rect x="204" y="196" width="24" height="86" />
      </g>
      <g fill="#f4efe7" opacity="0.9">
        <circle cx="690" cy="110" r="10" />
        <circle cx="900" cy="60" r="10" />
        <circle cx="470" cy="195" r="8" />
      </g>
    </svg>
  );
}

export function MetadataMapGraphic(): React.ReactElement {
  return (
    <svg className="h-full w-full" viewBox="0 0 760 460">
      <rect width="760" height="460" fill="#131e26" />
      <g opacity="0.22" stroke="#f4efe7" strokeWidth="1">
        <path d="M0 70 H760" />
        <path d="M0 140 H760" />
        <path d="M0 210 H760" />
        <path d="M0 280 H760" />
        <path d="M0 350 H760" />
        <path d="M95 0 V460" />
        <path d="M190 0 V460" />
        <path d="M285 0 V460" />
        <path d="M380 0 V460" />
        <path d="M475 0 V460" />
        <path d="M570 0 V460" />
        <path d="M665 0 V460" />
      </g>
      <g fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d="M40 330 C135 300 180 240 270 220 S420 220 570 120 S690 80 740 50" stroke="#b27340" strokeWidth="3.6" />
        <path d="M110 390 C185 360 260 295 330 290 S470 285 615 185" stroke="#f4efe7" strokeWidth="2.2" />
        <path d="M95 60 C170 120 220 180 280 225" stroke="#1f5a7e" strokeWidth="2.4" />
        <path d="M515 300 C540 240 575 198 610 166" stroke="#1f5a7e" strokeWidth="2.4" />
      </g>
      <g>
        <circle cx="270" cy="220" r="12" fill="#f4efe7" />
        <circle cx="570" cy="120" r="10" fill="#b27340" />
        <circle cx="615" cy="185" r="8" fill="#f4efe7" />
        <circle cx="330" cy="290" r="8" fill="#b27340" />
      </g>
    </svg>
  );
}

export function MetricSparkline({
  variant = "cobre",
}: {
  variant?: "cobre" | "laguna";
}): React.ReactElement {
  const stroke = variant === "laguna" ? "#1f5a7e" : "#b27340";

  return (
    <svg className="h-8 w-20" viewBox="0 0 84 32" fill="none">
      <path
        d="M2 24 L14 22 L24 18 L36 20 L46 10 L58 14 L70 8 L82 12"
        stroke={stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="46" cy="10" r="2.4" fill={stroke} />
      <circle cx="70" cy="8" r="2.4" fill={stroke} />
    </svg>
  );
}
