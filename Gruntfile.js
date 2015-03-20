module.exports = function(grunt) {

  "use strict";

  grunt.initConfig({

    srcFiles: ["src/static/purescript/*.purs"],

    psc: {
      options: {
        main: "Heatmap",
        modules: ["Heatmap"]
      },
      all: {
        src: ["<%=srcFiles%>"],
        dest: "src/static/dist/Main.js"
      }
    }
  });

  grunt.loadNpmTasks("grunt-purescript");

  grunt.registerTask("default", ["psc:all"]);

};
