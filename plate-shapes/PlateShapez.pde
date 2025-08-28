// New to coding? No worries. Processing may be the best way there is to learn. 
// <--- Anything with these 2 slashes is ignored by the program. They're secret messages from me to you <3
// Read them all, as they will guide you to set this up and customize it for yourself! 

// These are just global variables for both images so if you change the filename, you don't have to type it 100 times
PImage bgImg;
PImage overlayImg;

// --- You can customize these variables here ---
// your license plate image is your overlay, you'll want it to be nicely cropped, and a transparent png is ideal
String overlayImageName = "poo5000_500.png";
int numShapes = 15;
float minShapeSize = 0.25;
float maxShapeSize = 2;

// Define the license plate's exact size and position. This part is going to take a bit of trial and error
// You're going to want to make the license plate/overlay image nicely cover the plate in the background photo
// All values are in pixels, if you're going this with many images, I recommend aligning in PS or GIMP rather than guessing
int overlayWidth = 40;
int overlayHeight = 20;
int overlayX = 577; // X-coordinate from the left edge.
int overlayY = 537; // Y-coordinate from the top edge.
// -----------------------------------------------

void setup() {
  size(1500, 750);

  // Load a background image. It doesn't NEED to be of traffic, but it should at least be of a vehichle so it works across various ALPR models
  try {
    bgImg = loadImage("background.jpg");
    bgImg.resize(width, height);
  } catch (Exception e) {
    println("ERROR: 'background.jpg' not found in 'data' folder.");
  }

  // Load the overlay image.
  try {
    overlayImg = loadImage(overlayImageName);
    // Resize the loaded image to your defined dimensions.
    overlayImg.resize(overlayWidth, overlayHeight);
  } catch (Exception e) {
    println("ERROR: '" + overlayImageName + "' not found in 'data' folder.");
  }

  generateArtwork();
}

void draw() {
  // Empty; updates are event-driven by pressing Enter. But you could easily automate as many saved images as you need.
}

void keyPressed() {
  if (key == ENTER || key == RETURN) {
    println("Regenerating shapes and saving new image...");
    generateArtwork();
  }
}

/**
 * This function uses your static properties for the overlay that you put in above
 */
void generateArtwork() {
  // Exit if the required images are not loaded.
  if (bgImg == null || overlayImg == null) {
    background(255, 0, 0); // Red screen indicates a critical error.
    println("Cannot generate artwork. Please check that both images are in the 'data' folder.");
    return;
  }

  // 1. DRAW THE BACKGROUND
  background(bgImg);

  // 2. DRAW THE OVERLAY IMAGE
  // The position and size are now taken from the static variables at the top.
  image(overlayImg, overlayX, overlayY);

  // 3. SET THE CLIPPING RECTANGLE
  // This restricts drawing to the overlay's defined boundaries.
  clip(overlayX, overlayY, overlayWidth, overlayHeight);

  // 4. DRAW THE RANDOM SHAPES
  // Shapes will only appear inside the clipping rectangle.
  fill(0);
  noStroke();
  for (int i = 0; i < numShapes; i++) {
    // Generate a base position for the shape.
    float x = overlayX + random(overlayWidth);
    float y = overlayY + random(overlayHeight); // <-- Corrected this line.

    // Re-introducing the switch statement for shape variety.
    int shapeType = int(random(3)); // Pick a shape: 0, 1, or 2

    switch (shapeType) {
      case 0: // Draw a rectangle
        float rectW = random(minShapeSize, maxShapeSize);
        float rectH = random(minShapeSize, maxShapeSize);
        rect(x, y, rectW, rectH);
        break;

      case 1: // Draw an ellipse
        float ellipseW = random(minShapeSize, maxShapeSize);
        float ellipseH = random(minShapeSize, maxShapeSize);
        ellipse(x, y, ellipseW, ellipseH);
        break;

      case 2: // Draw a triangle
        // Define three points relative to the base (x, y) position.
        float x1 = x;
        float y1 = y;
        float x2 = x + random(-maxShapeSize * 2, maxShapeSize * 2);
        float y2 = y + random(-maxShapeSize * 2, maxShapeSize * 2);
        float x3 = x + random(-maxShapeSize * 2, maxShapeSize * 2);
        float y3 = y + random(-maxShapeSize * 2, maxShapeSize * 2);
        triangle(x1, y1, x2, y2, x3, y3);
        break;
    }
  }

  // 5. REMOVE THE CLIP
  // It's good practice to remove the clip when you're done with it.
  noClip();

  // 6. SAVE THE RESULT
  // Each time you press enter, a file is saved in your sketch directory. 
  // You can access this easily in Processing by pressing ctrl+K 
  String timestamp = year() + nf(month(), 2) + nf(day(), 2) + "-" +
                     nf(hour(), 2) + nf(minute(), 2) + nf(second(), 2);
  String filename = "Static-Overlay-Art-" + timestamp + ".png";
  save(filename);
  println("✓ Artwork saved as " + filename);
}
