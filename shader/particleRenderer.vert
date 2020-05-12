#version 450 core

in vec3 input_position; // positions where spheres are rendered
in vec3 input_vector; // vector field for color
in float input_scalar; // scalar field for color
in float input_radius; // size of each particle, if size per particle is enabled

uniform vec3 defaultColor; // particle color in color mode 0
uniform float brightness; // additional brightness control
uniform int colorMode; // 1: color by vector field direction, 2: color by vector field magnitude, 3: color by scalar field, 0: constant color
uniform float upperBound; // highest value of scalar field / vector field magnitude
uniform float lowerBound; // lowest value of scalar field / vector field magnitude
uniform mat4 model; // model matrix of the object
uniform bool enableSizePerParticle; // should every particle have a differnt size?
uniform float sphereRadius; // radius of the spheres when enableSizePerParticle is false
uniform bool customTransferFunc; // set to true to use the custom transfer function (the sampler 1D)
uniform sampler1D transferFunc; // the custom transfer function

out vec3 sphereColor;
out float particleRadius;

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

// used if no texture is set as the transfer function
// v is a value between 0 and 1
vec3 defaultTransferFunc(float v)
{
    return vec3((v*2.0f) +0.3f, (v) +0.1f, (0.5f*v) +0.1f);
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
        if(customTransferFunc)
            sphereColor = texture(transferFunc,leng).xyz;
        else
            sphereColor = defaultTransferFunc(leng);
        break;
    case 3: // scalar
        float rho = smoothstep(lowerBound , upperBound, input_scalar);
        if(customTransferFunc)
            sphereColor = texture(transferFunc,rho).xyz;
        else
            sphereColor = defaultTransferFunc(rho);
        break;
    case 0: // constant
    default:
        sphereColor = defaultColor;
        break;
    }

    if(enableSizePerParticle)
        particleRadius = input_radius;
    else
        particleRadius = sphereRadius;

    sphereColor *= brightness;
}