# Convenience functions to display inline graphics within GraphTerm

# Typical usage:
#   g <- gcairo()          # Initialize cairo device for output
#   x <- rnorm(100,0,1)
#   hist(x, col="blue")
#   g$frame()              # Display plot as inline image

require("RCurl")
require("Cairo")
require("png")

gcairo <- function(width=400, height=300, test=FALSE) {
  # Initialized window using Cairo graphics device with specified width/height
  # Returns list object with function gframe to display plot.
  #   gframe(overwrite=FALSE)
  gcat <- FALSE
  goverwrite <- FALSE
  cdev <- Cairo(width, height, type='raster')

  Cairo.onSave(cdev, function(dev, page) {
    if (!gcat)
      return()
    gsave(writePNG(Cairo.capture(cdev)), goverwrite, test=test)
    gcat <<- FALSE
    goverwrite <<- FALSE
  })

  list(frame = function(overwrite=FALSE) {
    gcat <<- TRUE
    goverwrite <<- overwrite
    frame()
  })
}

gsave <- function(pngdata, overwrite=FALSE, test=False) {
  # Displays PNG image data within a GtaphTerm pagelet
  prefix <- paste("\x1b[?1155;", Sys.getenv("GTERM_COOKIE"), "h", sep="")
  suffix <- "\x1b[?1155;l"

  image64 <- base64(pngdata)

  # Create image blob
  blobid = paste(sample(1:1000000,1), sample(1:1000000,1), sep="")
  imagepfx <- paste('<!--gterm data blob=', blobid, '-->image/png;base64,', sep='')
  cat(prefix, imagepfx, image64, suffix, sep="")

  if (overwrite) {
    overs = ' overwrite=yes'
  } else {
    overs = ''
  }

  # Display blob
  pagelet <- paste('<!--gterm pagelet display=block blob=', blobid, overs, '--><div class="gterm-blockhtml"><img class="gterm-blockimg" src="/_blob/local/', blobid, '"></div>', sep='')
  if (test) {
    cat(pagelet, " page=", page, sep="")
  } else {
    cat(prefix, pagelet, suffix, sep="")
  }
}
  
gshow <- function(overwrite=FALSE) {
  gsave(writePNG(dev.capture(native=TRUE)), overwrite)
}

gpng <- function(width=400, height=300, test=FALSE) {
  # Alternative approach to displaying plot
  png(filename="gterm_tem.png", width=width, height=height)
  setHook("plot.new", function() {
    ## Does not work until second plot
    ## gsave(readBin("gterm_tem.png",what="raw",n=2e6), test=test)
  })
}
