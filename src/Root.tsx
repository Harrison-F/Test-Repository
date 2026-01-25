import { Composition } from "remotion";
import { HelloWorld } from "./HelloWorld";
import { GalleryShowcase } from "./GalleryShowcase";
import { FreedomLabIntro } from "./FreedomLabIntro";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Basic Hello World example - great for learning */}
      <Composition
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          titleText: "Welcome to Remotion",
          titleColor: "#ffffff",
        }}
      />

      {/* Gallery showcase - themed for Fat Cat Gallery */}
      <Composition
        id="GalleryShowcase"
        component={GalleryShowcase}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          galleryName: "Fat Cat Gallery",
        }}
      />

      {/* Freedom Lab NYC intro - retro pixel style */}
      <Composition
        id="FreedomLabIntro"
        component={FreedomLabIntro}
        durationInFrames={180}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
