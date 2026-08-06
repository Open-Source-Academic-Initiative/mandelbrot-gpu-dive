import sys
import numpy as np
from vispy import app, gloo

VERTEX_SHADER = """
attribute vec2 a_position;
varying vec2 v_position;
void main() {
    v_position = a_position;
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
varying vec2 v_position;

uniform vec2 u_center;
uniform vec2 u_scale;
uniform int u_max_iter;
uniform float u_time;

void main() {
    vec2 c = u_center + v_position * u_scale;
    vec2 z = vec2(0.0, 0.0);
    int iters = 0;
    
    float x = 0.0;
    float y = 0.0;
    
    for (int i = 0; i < 5000; i++) {
        if (i >= u_max_iter) break;
        
        x = (z.x * z.x - z.y * z.y) + c.x;
        y = (2.0 * z.x * z.y) + c.y;
        
        if ((x * x + y * y) > 4.0) {
            iters = i;
            break;
        }
        z.x = x;
        z.y = y;
        iters = i + 1;
    }
    
    if (iters == u_max_iter) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        float mag2 = x * x + y * y;
        float smooth_iters = float(iters) + 1.0 - log2(log(mag2) * 1.442695); 
        
        // Add u_time to make the colors flow and animate continuously
        float r = sin(smooth_iters * 0.15 + u_time * 2.0) * 0.5 + 0.5;
        float g = sin(smooth_iters * 0.15 + 2.09 + u_time * 1.5) * 0.5 + 0.5;
        float b = sin(smooth_iters * 0.15 + 4.18 + u_time * 2.5) * 0.5 + 0.5;
        gl_FragColor = vec4(r, g, b, 1.0);
    }
}
"""

class MandelbrotCanvas(app.Canvas):
    def __init__(self):
        super(MandelbrotCanvas, self).__init__(title='Mandelbrot Set (Cinematic GPU Dive)', 
                                               size=(1024, 768), 
                                               keys='interactive')
        
        self.program = gloo.Program(VERTEX_SHADER, FRAGMENT_SHADER)
        
        self.program['a_position'] = np.array([
            [-1.0, -1.0], [ 1.0, -1.0],
            [-1.0,  1.0], [ 1.0,  1.0]
        ], dtype=np.float32)
        
        # A curated list of beautiful locations to dive into
        self.targets = [
            np.array([-0.743643887037151, 0.131825904205330], dtype=np.float32), # Seahorse Valley
            np.array([0.286931868895045, 0.014286693904085], dtype=np.float32),  # Elephant Valley
            np.array([-1.769383179195515, 0.004236847918736], dtype=np.float32), # Mini Mandelbrot
            np.array([-0.101096363845620, 0.956286510809141], dtype=np.float32), # Scepter Valley
            np.array([-0.748, 0.1], dtype=np.float32)                            # Swirls
        ]
        self.target_idx = 0
        
        self.center = np.array([-0.75, 0.0], dtype=np.float32)
        self.base_scale = np.array([1.75 * (1024/768), 1.75], dtype=np.float32)
        self.scale = self.base_scale.copy()
        self.max_iter = 100
        self.time = 0.0
        self.zoom_dir = -1 # -1 = zooming in, 1 = zooming out
        
        self.program['u_center'] = self.center
        self.program['u_scale'] = self.scale
        self.program['u_max_iter'] = self.max_iter
        self.program['u_time'] = self.time
        
        gloo.set_state(clear_color='black', blend=False)
        self.show()
        
        # Start a 60 FPS timer for the animation
        self.timer = app.Timer('auto', connect=self.on_timer, start=True)

    def on_timer(self, event):
        target = self.targets[self.target_idx]
        self.time += 0.016
        
        if self.zoom_dir == -1:
            # Smoothly glide the center towards the target
            self.center = self.center * 0.97 + target * 0.03
            # Zoom in by 1.5% each frame
            self.scale *= 0.985
            # Dynamically increase calculation detail as we get deeper
            self.max_iter = min(1500, int(self.max_iter + 2))
            
            # Turn around when we reach the float32 precision limit (pixelation)
            if self.scale[1] < 2e-6:
                self.zoom_dir = 1
        else:
            # Zoom out faster
            self.scale *= 1.05
            self.max_iter = max(100, int(self.max_iter - 5))
            
            # Once fully zoomed out, move to the next cool location!
            if self.scale[1] > 1.75:
                self.zoom_dir = -1
                self.target_idx = (self.target_idx + 1) % len(self.targets)
                self.scale = self.base_scale.copy()
                self.center = np.array([-0.75, 0.0], dtype=np.float32)
        
        self.program['u_center'] = self.center
        self.program['u_scale'] = self.scale
        self.program['u_max_iter'] = self.max_iter
        self.program['u_time'] = self.time
        self.update()

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('triangle_strip')

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)
        width, height = event.physical_size
        aspect = width / height
        self.base_scale[0] = self.base_scale[1] * aspect
        self.scale[0] = self.scale[1] * aspect
        self.program['u_scale'] = self.scale
        self.update()

if __name__ == '__main__':
    app.use_app('pyglet')
    canvas = MandelbrotCanvas()
    app.run()
