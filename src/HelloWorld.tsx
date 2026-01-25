import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface HelloWorldProps {
  titleText: string;
  titleColor: string;
}

export const HelloWorld: React.FC<HelloWorldProps> = ({
  titleText,
  titleColor,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Spring animation for the title entrance
  const titleScale = spring({
    frame,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
      mass: 0.5,
    },
  });

  // Fade in effect
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Fade out at the end
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 30, durationInFrames],
    [1, 0],
    {
      extrapolateLeft: "clamp",
    }
  );

  // Subtle rotation animation
  const rotation = interpolate(frame, [0, durationInFrames], [0, 360]);

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        justifyContent: "center",
        alignItems: "center",
        opacity: opacity * fadeOut,
      }}
    >
      {/* Animated background circles */}
      <div
        style={{
          position: "absolute",
          width: 400,
          height: 400,
          borderRadius: "50%",
          border: "2px solid rgba(255, 215, 0, 0.3)",
          transform: `rotate(${rotation}deg)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 500,
          height: 500,
          borderRadius: "50%",
          border: "2px solid rgba(255, 215, 0, 0.2)",
          transform: `rotate(-${rotation}deg)`,
        }}
      />

      {/* Main title */}
      <h1
        style={{
          color: titleColor,
          fontSize: 100,
          fontFamily: "Arial, sans-serif",
          fontWeight: "bold",
          textAlign: "center",
          transform: `scale(${titleScale})`,
          textShadow: "0 4px 20px rgba(255, 215, 0, 0.5)",
        }}
      >
        {titleText}
      </h1>

      {/* Subtitle */}
      <p
        style={{
          position: "absolute",
          bottom: 200,
          color: "#ffd700",
          fontSize: 32,
          fontFamily: "Arial, sans-serif",
          opacity: interpolate(frame, [30, 60], [0, 1], {
            extrapolateRight: "clamp",
          }),
        }}
      >
        Create videos with code
      </p>
    </AbsoluteFill>
  );
};
