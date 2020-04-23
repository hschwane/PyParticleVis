#version 450 core

in vec3 input_position; // positions where spheres are rendered
in vec3 input_vector; // vector field for color
in float input_scalar; // scalar field for color

uniform vec3 defaultColor; // particle color in color mode 5
uniform float brightness; // additional brightness control
uniform int colorMode; // 1: color by vector field direction, 2: color by vector field magnitude, 3: color by scalar field, 0: constant color
uniform float upperBound; // highest value of scalar field / vector field magnitude
uniform float lowerBound; // lowest value of scalar field / vector field magnitude
uniform mat4 model; // model matrix of the object

out vec3 sphereColor;

// some helper functions
bool iszero(float f)
{
    return (abs(f)<5.96046449e-8);
}

bool iszero(vec2 v)
{
    return iszero(length(v));
}

bool iszero(vec3 v)
{
    return iszero(length(v));
}

// see https://github.com/tdd11235813/spheres_shader/tree/master/src/shader
// and: https://paroj.github.io/gltut/Illumination/Tutorial%2013.html
// as well as chapter 14 and 15
// for sphere imposter rendering
void main()
{
	gl_Position = model * vec4(input_position.xyz,1.0);

    switch(colorMode)
    {
    case 1: // vector field direction
        if(iszero(input_vector))
            sphereColor = defaultColor;
        else
        {
            sphereColor = 0.5f*normalize(input_vector)+vec3(0.5f);
        }
        break;
    case 2: // vector magnitude
        float leng = smoothstep(lowerBound,upperBound,length(input_vector));
        sphereColor = vec3((leng*2.0f) +0.3f, (leng) +0.1f, (0.5f*leng) +0.1f);
        break;
    case 3: // scalar
        float rho = smoothstep(lowerBound , upperBound, input_scalar);
        sphereColor = vec3((rho*2.0f) +0.3f, (rho) +0.1f, (0.5f*rho) +0.1f);
        break;
    case 0: // constant
    default:
        sphereColor = defaultColor;
        break;
    }

    sphereColor *= brightness;
}