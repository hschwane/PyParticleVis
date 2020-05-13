#version 330

in vec3 input_position;

uniform mat4 view; // view / camera matrix
uniform mat4 projection; // projection matrix
out vec3 color;

void main()
{
    if(gl_VertexID < 2)
        color = vec3(1,0,0);
    else if(gl_VertexID < 4)
        color = vec3(0,1,0);
    else
        color = vec3(0,0,1);

    gl_Position = projection * view * vec4(input_position,1);
}
