import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

// Pixelated torch component with flickering flame
const PixelTorch: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Torch entrance animation
  const torchEntrance = spring({
    frame,
    fps,
    config: { damping: 100, stiffness: 80 },
  });

  const torchX = interpolate(torchEntrance, [0, 1], [-300, 0]);

  // Flame flicker effect
  const flicker1 = Math.sin(frame * 0.5) * 3;
  const flicker2 = Math.cos(frame * 0.7) * 2;
  const flameScale = 1 + Math.sin(frame * 0.3) * 0.05;

  return (
    <div
      style={{
        position: "absolute",
        left: 20,
        bottom: 0,
        transform: `translateX(${torchX}px)`,
      }}
    >
      {/* Torch handle */}
      <svg width="200" height="800" viewBox="0 0 200 800">
        {/* Hand/grip - pixelated */}
        <rect x="70" y="600" width="60" height="120" fill="#1a8c4a" />
        <rect x="60" y="620" width="20" height="80" fill="#1a8c4a" />
        <rect x="120" y="620" width="20" height="80" fill="#1a8c4a" />
        <rect x="50" y="640" width="20" height="60" fill="#1a8c4a" />
        <rect x="130" y="640" width="20" height="60" fill="#1a8c4a" />

        {/* Torch shaft */}
        <rect x="80" y="350" width="40" height="250" fill="#1a8c4a" />
        <rect x="75" y="340" width="50" height="20" fill="#1a8c4a" />

        {/* Torch cup/base */}
        <rect x="50" y="280" width="100" height="60" fill="#1a8c4a" />
        <rect x="40" y="290" width="120" height="40" fill="#156b3a" />
        <rect x="55" y="270" width="90" height="20" fill="#1a8c4a" />

        {/* Decorative bands on cup */}
        <rect x="45" y="300" width="110" height="8" fill="#0d4d2a" />
        <rect x="45" y="315" width="110" height="8" fill="#0d4d2a" />

        {/* Flame group with animation */}
        <g
          transform={`translate(${flicker1}, ${flicker2}) scale(${flameScale})`}
          style={{ transformOrigin: "100px 200px" }}
        >
          {/* Outer flame glow */}
          <ellipse cx="100" cy="180" rx="50" ry="80" fill="#2d8c4a" opacity="0.3" />

          {/* Main flame - pixelated style */}
          <rect x="70" y="200" width="60" height="60" fill="#22c55e" />
          <rect x="60" y="160" width="80" height="50" fill="#22c55e" />
          <rect x="70" y="120" width="60" height="50" fill="#4ade80" />
          <rect x="80" y="80" width="40" height="50" fill="#4ade80" />
          <rect x="85" y="50" width="30" height="40" fill="#86efac" />
          <rect x="90" y="20" width="20" height="40" fill="#bbf7d0" />

          {/* Flame tips */}
          <rect x="75" y="100" width="15" height="30" fill="#86efac" />
          <rect x="110" y="110" width="15" height="25" fill="#86efac" />
          <rect x="65" y="140" width="10" height="20" fill="#4ade80" />
          <rect x="125" y="150" width="10" height="15" fill="#4ade80" />
        </g>
      </svg>
    </div>
  );
};

// NYC Skyline silhouette
const Skyline: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle parallax movement
  const parallax = interpolate(frame, [0, 300], [0, -20], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: "60%",
        transform: `translateX(${parallax}px)`,
      }}
    >
      <svg width="100%" height="100%" viewBox="0 0 1920 600" preserveAspectRatio="xMidYMax slice">
        {/* Background buildings - darker */}
        <rect x="100" y="200" width="80" height="400" fill="#0a1628" />
        <rect x="200" y="150" width="100" height="450" fill="#0c1a2e" />
        <rect x="350" y="250" width="70" height="350" fill="#0a1628" />
        <rect x="450" y="100" width="120" height="500" fill="#0c1a2e" />
        <rect x="600" y="180" width="90" height="420" fill="#0a1628" />
        <rect x="750" y="220" width="80" height="380" fill="#0c1a2e" />
        <rect x="900" y="80" width="100" height="520" fill="#0a1628" />
        <rect x="1050" y="200" width="110" height="400" fill="#0c1a2e" />
        <rect x="1200" y="150" width="90" height="450" fill="#0a1628" />
        <rect x="1350" y="250" width="100" height="350" fill="#0c1a2e" />
        <rect x="1500" y="180" width="120" height="420" fill="#0a1628" />
        <rect x="1680" y="220" width="80" height="380" fill="#0c1a2e" />
        <rect x="1800" y="160" width="120" height="440" fill="#0a1628" />

        {/* Window lights - subtle yellow dots */}
        {[...Array(60)].map((_, i) => {
          const x = 120 + (i % 15) * 120 + Math.random() * 40;
          const y = 250 + Math.floor(i / 15) * 80 + Math.random() * 30;
          const opacity = 0.3 + Math.sin(frame * 0.1 + i) * 0.2;
          return (
            <rect
              key={i}
              x={x}
              y={y}
              width="4"
              height="6"
              fill="#fbbf24"
              opacity={opacity}
            />
          );
        })}
      </svg>
    </div>
  );
};

// Animated pixel text
const PixelText: React.FC<{ text: string; delay: number; y: number }> = ({
  text,
  delay,
  y,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        position: "absolute",
        top: y,
        left: 0,
        right: 0,
      }}
    >
      {text.split("").map((char, index) => {
        const charDelay = delay + index * 3;
        const charSpring = spring({
          frame: frame - charDelay,
          fps,
          config: { damping: 12, stiffness: 200 },
        });

        const scale = interpolate(charSpring, [0, 1], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const opacity = interpolate(charSpring, [0, 0.5], [0, 1], {
          extrapolateRight: "clamp",
        });

        // Glitch effect on entrance
        const glitchX = frame - charDelay < 10 ? (Math.random() - 0.5) * 10 : 0;
        const glitchY = frame - charDelay < 10 ? (Math.random() - 0.5) * 5 : 0;

        return (
          <span
            key={index}
            style={{
              display: "inline-block",
              fontFamily: "'Press Start 2P', 'Courier New', monospace",
              fontSize: 90,
              fontWeight: "bold",
              color: "#22c55e",
              textShadow: `
                0 0 20px rgba(34, 197, 94, 0.8),
                0 0 40px rgba(34, 197, 94, 0.5),
                4px 4px 0 #0d4d2a
              `,
              transform: `scale(${scale}) translate(${glitchX}px, ${glitchY}px)`,
              opacity,
              marginRight: char === " " ? 30 : 8,
            }}
          >
            {char}
          </span>
        );
      })}
    </div>
  );
};

// Scanline effect overlay
const Scanlines: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          rgba(0, 0, 0, 0.1) 2px,
          rgba(0, 0, 0, 0.1) 4px
        )`,
        pointerEvents: "none",
        opacity: 0.5,
      }}
    />
  );
};

// CRT flicker effect
const CRTFlicker: React.FC = () => {
  const frame = useCurrentFrame();
  const flicker = Math.random() > 0.97 ? 0.95 : 1;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "white",
        opacity: 1 - flicker,
        pointerEvents: "none",
      }}
    />
  );
};

export const FreedomLabIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Background fade in
  const bgOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0f172a",
        opacity: bgOpacity,
      }}
    >
      {/* Gradient background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(
            180deg,
            #1e3a5f 0%,
            #0f172a 40%,
            #0a0f1a 100%
          )`,
        }}
      />

      {/* NYC Skyline */}
      <Skyline />

      {/* Torch */}
      <PixelTorch />

      {/* Main text */}
      <Sequence from={20}>
        <PixelText text="FREEDOM" delay={0} y={280} />
      </Sequence>

      <Sequence from={40}>
        <PixelText text="LAB NYC" delay={0} y={400} />
      </Sequence>

      {/* Tagline */}
      <Sequence from={90}>
        <div
          style={{
            position: "absolute",
            bottom: 120,
            left: 0,
            right: 0,
            textAlign: "center",
          }}
        >
          <p
            style={{
              fontFamily: "'Courier New', monospace",
              fontSize: 24,
              color: "#94a3b8",
              letterSpacing: "0.3em",
              opacity: interpolate(frame - 90, [0, 30], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            BUILDING THE FUTURE
          </p>
        </div>
      </Sequence>

      {/* Retro effects */}
      <Scanlines />
      <CRTFlicker />
    </AbsoluteFill>
  );
};
