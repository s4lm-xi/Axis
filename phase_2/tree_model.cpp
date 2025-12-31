int classify(float x[]) {
  if (x[2] <= 0.016562) {
    if (x[0] <= 0.350017) {
      if (x[1] <= 0.702566) {
        return 0;
      } else {
        if (x[4] <= -1.619375) {
          return 1;
        } else {
          return 1;
        }
      }
    } else {
      if (x[1] <= 0.703507) {
        return 1;
      } else {
        if (x[2] <= -1.571867) {
          return 2;
        } else {
          return 2;
        }
      }
    }
  } else {
    if (x[1] <= 0.705110) {
      if (x[0] <= 0.346753) {
        if (x[2] <= 1.723228) {
          return 1;
        } else {
          return 1;
        }
      } else {
        if (x[1] <= -1.628076) {
          return 2;
        } else {
          return 2;
        }
      }
    } else {
      if (x[0] <= 0.352320) {
        if (x[0] <= -1.635495) {
          return 2;
        } else {
          return 2;
        }
      } else {
        return 3;
      }
    }
  }
}