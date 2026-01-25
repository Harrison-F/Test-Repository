import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
} from "remotion";

interface GalleryShowcaseProps {
  galleryName: string;
}

// Intro scene component
const IntroScene: React.FC<{ galleryName: string }> = ({ galleryName }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 100, stiffness: 200, mass: 0.5 },
  });

  const subtitleOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #000000 0%, #1a1a1a 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h1
          style={{
            color: "#ffd700",
            fontSize: 120,
            fontFamily: "'Playfair Display', serif",
            fontWeight: "bold",
            transform: `scale(${titleScale})`,
            marginBottom: 20,
            textShadow: "0 0 40px rgba(255, 215, 0, 0.5)",
          }}
        >
          {galleryName}
        </h1>
        <p
          style={{
            color: "#ffffff",
            fontSize: 36,
            fontFamily: "'Roboto', sans-serif",
            opacity: subtitleOpacity,
            letterSpacing: "0.3em",
          }}
        >
          PRESENTS
        </p>
      </div>
    </AbsoluteFill>
  );
};

// Featured artwork scene
const ArtworkScene: React.FC<{
  title: string;
  artist: string;
  year: string;
  index: number;
}> = ({ title, artist, year, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideIn = spring({
    frame,
    fps,
    config: { damping: 80, stiffness: 100, mass: 0.8 },
  });

  const textOpacity = interpolate(frame, [20, 50], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Alternate slide direction based on index
  const slideDirection = index % 2 === 0 ? 1 : -1;
  const translateX = interpolate(slideIn, [0, 1], [100 * slideDirection, 0]);

  return (
    <AbsoluteFill
      style={{
        background: "#0a0a0a",
        flexDirection: "row",
      }}
    >
      {/* Artwork placeholder area */}
      <div
        style={{
          flex: 1,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `translateX(${translateX}px)`,
        }}
      >
        <div
          style={{
            width: 700,
            height: 700,
            background: `linear-gradient(${45 + index * 30}deg, #2a2a2a, #1a1a1a)`,
            border: "8px solid #ffd700",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            boxShadow: "0 20px 60px rgba(0, 0, 0, 0.8)",
          }}
        >
          <span style={{ color: "#444", fontSize: 48, fontFamily: "serif" }}>
            Artwork {index + 1}
          </span>
        </div>
      </div>

      {/* Info panel */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: 80,
          opacity: textOpacity,
        }}
      >
        <h2
          style={{
            color: "#ffd700",
            fontSize: 64,
            fontFamily: "'Playfair Display', serif",
            marginBottom: 20,
            lineHeight: 1.2,
          }}
        >
          {title}
        </h2>
        <p
          style={{
            color: "#cccccc",
            fontSize: 32,
            fontFamily: "'Roboto', sans-serif",
            marginBottom: 10,
          }}
        >
          by {artist}
        </p>
        <p
          style={{
            color: "#888888",
            fontSize: 24,
            fontFamily: "'Roboto', sans-serif",
          }}
        >
          {year}
        </p>
      </div>
    </AbsoluteFill>
  );
};

// Outro scene
const OutroScene: React.FC<{ galleryName: string }> = ({ galleryName }) => {
  const frame = useCurrentFrame();

  const fadeIn = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "#000000",
        justifyContent: "center",
        alignItems: "center",
        opacity: fadeIn,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h2
          style={{
            color: "#ffd700",
            fontSize: 72,
            fontFamily: "'Playfair Display', serif",
            marginBottom: 40,
          }}
        >
          {galleryName}
        </h2>
        <p
          style={{
            color: "#888888",
            fontSize: 28,
            fontFamily: "'Roboto', sans-serif",
            letterSpacing: "0.2em",
          }}
        >
          VISIT US TODAY
        </p>
        <div
          style={{
            marginTop: 60,
            width: 100,
            height: 2,
            background: "#ffd700",
            margin: "60px auto 0",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const GalleryShowcase: React.FC<GalleryShowcaseProps> = ({
  galleryName,
}) => {
  // Sample artworks - you can replace these with real data
  const artworks = [
    { title: "Whispers of Gold", artist: "Elena Vasquez", year: "2024" },
    { title: "Midnight Reverie", artist: "Marcus Chen", year: "2023" },
    { title: "Abstract Dreams", artist: "Sophie Laurent", year: "2024" },
  ];

  return (
    <AbsoluteFill>
      {/* Intro - 3 seconds (frames 0-89) */}
      <Sequence from={0} durationInFrames={90}>
        <IntroScene galleryName={galleryName} />
      </Sequence>

      {/* Artwork scenes - 2 seconds each (60 frames each) */}
      {artworks.map((artwork, index) => (
        <Sequence
          key={artwork.title}
          from={90 + index * 60}
          durationInFrames={60}
        >
          <ArtworkScene
            title={artwork.title}
            artist={artwork.artist}
            year={artwork.year}
            index={index}
          />
        </Sequence>
      ))}

      {/* Outro - remaining frames */}
      <Sequence from={270} durationInFrames={30}>
        <OutroScene galleryName={galleryName} />
      </Sequence>
    </AbsoluteFill>
  );
};
