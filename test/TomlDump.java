import com.electronwill.nightconfig.toml.TomlParser;
public class TomlDump {
  public static void main(String[] a) throws Exception {
    var c = new TomlParser().parse(new java.io.FileInputStream(a[0]));
    System.out.println("parsed OK. contains 'mods': " + c.contains("mods"));
    System.out.println("mods[0] modId=" + c.get("mods[0].modId") + " version=" + c.get("mods[0].version"));
  }
}